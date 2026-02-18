using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Services;

/// <summary>
/// Implementation of the BOQ roll-up service.
/// Calculates totals at the correct hierarchy level based on the tender's pricing level.
/// </summary>
public class BoqRollUpService : IBoqRollUpService
{
    private readonly IApplicationDbContext _context;

    public BoqRollUpService(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<PriceableNodes> GetPriceableNodeIdsAsync(
        Guid tenderId, CancellationToken ct = default)
    {
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == tenderId, ct)
            ?? throw new KeyNotFoundException($"Tender {tenderId} not found.");

        var result = new PriceableNodes { PricingLevel = tender.PricingLevel };

        switch (tender.PricingLevel)
        {
            case PricingLevel.Bill:
                // Priceable nodes are top-level sections (bills)
                result.SectionIds = await _context.BoqSections
                    .Where(s => s.TenderId == tenderId && s.ParentSectionId == null)
                    .OrderBy(s => s.SortOrder)
                    .Select(s => s.Id)
                    .ToListAsync(ct);
                break;

            case PricingLevel.Item:
                // Priceable nodes are top-level items (no parent)
                result.ItemIds = await _context.BoqItems
                    .Where(i => i.TenderId == tenderId && i.ParentItemId == null)
                    .OrderBy(i => i.SortOrder)
                    .Select(i => i.Id)
                    .ToListAsync(ct);
                break;

            case PricingLevel.SubItem:
                // Priceable nodes are all leaf items (non-groups)
                result.ItemIds = await _context.BoqItems
                    .Where(i => i.TenderId == tenderId && !i.IsGroup)
                    .OrderBy(i => i.SortOrder)
                    .Select(i => i.Id)
                    .ToListAsync(ct);
                break;
        }

        return result;
    }

    public async Task<decimal> CalculateGrandTotalAsync(
        Guid tenderId, Guid bidSubmissionId, CancellationToken ct = default)
    {
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == tenderId, ct)
            ?? throw new KeyNotFoundException($"Tender {tenderId} not found.");

        return tender.PricingLevel switch
        {
            PricingLevel.Bill => await _context.BidPricings
                .Where(bp => bp.BidSubmissionId == bidSubmissionId
                    && bp.BoqSectionId != null
                    && bp.IsIncludedInTotal)
                .SumAsync(bp => bp.NormalizedAmount ?? 0m, ct),

            PricingLevel.Item => await _context.BidPricings
                .Where(bp => bp.BidSubmissionId == bidSubmissionId
                    && bp.BoqItemId != null
                    && bp.IsIncludedInTotal)
                .Join(
                    _context.BoqItems.Where(i => i.TenderId == tenderId && i.ParentItemId == null),
                    bp => bp.BoqItemId,
                    i => i.Id,
                    (bp, i) => bp)
                .SumAsync(bp => bp.NormalizedAmount ?? 0m, ct),

            PricingLevel.SubItem => await _context.BidPricings
                .Where(bp => bp.BidSubmissionId == bidSubmissionId
                    && bp.BoqItemId != null
                    && bp.IsIncludedInTotal)
                .Join(
                    _context.BoqItems.Where(i => i.TenderId == tenderId && !i.IsGroup),
                    bp => bp.BoqItemId,
                    i => i.Id,
                    (bp, i) => bp)
                .SumAsync(bp => bp.NormalizedAmount ?? 0m, ct),

            _ => 0m
        };
    }

    public async Task<List<BillTotal>> CalculateBillTotalsAsync(
        Guid tenderId, Guid bidSubmissionId, CancellationToken ct = default)
    {
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == tenderId, ct)
            ?? throw new KeyNotFoundException($"Tender {tenderId} not found.");

        // Get all top-level sections (bills)
        var bills = await _context.BoqSections
            .Where(s => s.TenderId == tenderId && s.ParentSectionId == null)
            .OrderBy(s => s.SortOrder)
            .Select(s => new { s.Id, s.SectionNumber, s.Title })
            .ToListAsync(ct);

        var result = new List<BillTotal>();

        foreach (var bill in bills)
        {
            decimal total;

            if (tender.PricingLevel == PricingLevel.Bill)
            {
                // Bill-level pricing: sum of bid_pricing rows keyed by section
                total = await _context.BidPricings
                    .Where(bp => bp.BidSubmissionId == bidSubmissionId
                        && bp.BoqSectionId == bill.Id
                        && bp.IsIncludedInTotal)
                    .SumAsync(bp => bp.NormalizedAmount ?? 0m, ct);
            }
            else
            {
                // Item or SubItem level: sum all pricing rows for items in this bill's section tree
                var sectionIds = await GetSectionTreeIdsAsync(bill.Id, tenderId, ct);

                total = await _context.BidPricings
                    .Where(bp => bp.BidSubmissionId == bidSubmissionId
                        && bp.BoqItemId != null
                        && bp.IsIncludedInTotal)
                    .Join(
                        _context.BoqItems.Where(i => sectionIds.Contains(i.SectionId)),
                        bp => bp.BoqItemId,
                        i => i.Id,
                        (bp, i) => bp)
                    .SumAsync(bp => bp.NormalizedAmount ?? 0m, ct);
            }

            result.Add(new BillTotal
            {
                SectionId = bill.Id,
                SectionNumber = bill.SectionNumber,
                Title = bill.Title,
                Total = total
            });
        }

        return result;
    }

    public async Task<List<ItemTotal>> CalculateItemTotalsAsync(
        Guid tenderId, Guid bidSubmissionId, CancellationToken ct = default)
    {
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == tenderId, ct)
            ?? throw new KeyNotFoundException($"Tender {tenderId} not found.");

        // Only meaningful at sub-item level — group items aggregate their children
        if (tender.PricingLevel != PricingLevel.SubItem)
        {
            return new List<ItemTotal>();
        }

        // Get all top-level items (both groups and standalone)
        var topItems = await _context.BoqItems
            .Where(i => i.TenderId == tenderId && i.ParentItemId == null)
            .OrderBy(i => i.SortOrder)
            .Select(i => new { i.Id, i.ItemNumber, i.Description, i.SectionId, i.IsGroup })
            .ToListAsync(ct);

        // Fetch all child items upfront to avoid N+1 queries
        var allChildItems = await _context.BoqItems
            .Where(i => i.TenderId == tenderId && i.ParentItemId != null)
            .Select(i => new { i.Id, i.ParentItemId })
            .ToListAsync(ct);

        var childItemsByParent = allChildItems
            .GroupBy(i => i.ParentItemId!.Value)
            .ToDictionary(g => g.Key, g => g.Select(x => x.Id).ToList());

        var result = new List<ItemTotal>();

        foreach (var item in topItems)
        {
            decimal total;

            if (item.IsGroup && childItemsByParent.TryGetValue(item.Id, out var childItemIds))
            {
                // Sum all child items' pricing
                total = await _context.BidPricings
                    .Where(bp => bp.BidSubmissionId == bidSubmissionId
                        && bp.BoqItemId != null
                        && childItemIds.Contains(bp.BoqItemId!.Value)
                        && bp.IsIncludedInTotal)
                    .SumAsync(bp => bp.NormalizedAmount ?? 0m, ct);
            }
            else
            {
                // Standalone item — its own pricing
                total = await _context.BidPricings
                    .Where(bp => bp.BidSubmissionId == bidSubmissionId
                        && bp.BoqItemId == item.Id
                        && bp.IsIncludedInTotal)
                    .SumAsync(bp => bp.NormalizedAmount ?? 0m, ct);
            }

            result.Add(new ItemTotal
            {
                ItemId = item.Id,
                ItemNumber = item.ItemNumber,
                Description = item.Description,
                SectionId = item.SectionId,
                Total = total,
                IsGroup = item.IsGroup
            });
        }

        return result;
    }

    /// <summary>
    /// Gets all section IDs in a section's subtree (the section itself + all descendants).
    /// </summary>
    private async Task<List<Guid>> GetSectionTreeIdsAsync(
        Guid rootSectionId, Guid tenderId, CancellationToken ct)
    {
        var allSections = await _context.BoqSections
            .Where(s => s.TenderId == tenderId)
            .Select(s => new { s.Id, s.ParentSectionId })
            .ToListAsync(ct);

        var result = new List<Guid> { rootSectionId };
        var queue = new Queue<Guid>();
        queue.Enqueue(rootSectionId);

        while (queue.Count > 0)
        {
            var parentId = queue.Dequeue();
            var children = allSections
                .Where(s => s.ParentSectionId == parentId)
                .Select(s => s.Id);

            foreach (var childId in children)
            {
                result.Add(childId);
                queue.Enqueue(childId);
            }
        }

        return result;
    }
}
