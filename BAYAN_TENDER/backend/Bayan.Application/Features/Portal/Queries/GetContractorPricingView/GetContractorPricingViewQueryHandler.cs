using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.Services;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Queries.GetContractorPricingView;

/// <summary>
/// Handler for GetContractorPricingViewQuery.
/// Builds the pricing tree based on the tender's pricing level and loads any existing draft.
/// </summary>
public class GetContractorPricingViewQueryHandler
    : IRequestHandler<GetContractorPricingViewQuery, ContractorPricingViewDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IBoqRollUpService _rollUpService;

    public GetContractorPricingViewQueryHandler(
        IApplicationDbContext context,
        IBoqRollUpService rollUpService)
    {
        _context = context;
        _rollUpService = rollUpService;
    }

    public async Task<ContractorPricingViewDto?> Handle(
        GetContractorPricingViewQuery request,
        CancellationToken cancellationToken)
    {
        // 1. Validate bidder access
        var tenderBidder = await _context.TenderBidders
            .AsNoTracking()
            .FirstOrDefaultAsync(
                tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId,
                cancellationToken);

        if (tenderBidder == null || tenderBidder.QualificationStatus == QualificationStatus.Removed)
        {
            throw new UnauthorizedAccessException("You do not have access to this tender.");
        }

        // 2. Load tender to get pricing level
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            return null;
        }

        // 3. Get priceable node IDs via roll-up service
        var priceableNodes = await _rollUpService.GetPriceableNodeIdsAsync(
            request.TenderId, cancellationToken);

        // 4. Load BOQ structure (sections + items)
        var sections = await _context.BoqSections
            .Where(s => s.TenderId == request.TenderId)
            .Include(s => s.Items.OrderBy(i => i.SortOrder))
                .ThenInclude(i => i.ChildItems.OrderBy(c => c.SortOrder))
            .AsNoTracking()
            .OrderBy(s => s.SortOrder)
            .ToListAsync(cancellationToken);

        // 5. Build pricing tree based on pricing level
        var nodes = BuildPricingTree(sections, tender.PricingLevel, priceableNodes);

        // 6. Load existing draft
        var draftSubmission = await _context.BidSubmissions
            .AsNoTracking()
            .FirstOrDefaultAsync(
                bs => bs.TenderId == request.TenderId
                    && bs.BidderId == request.BidderId
                    && bs.Status == BidSubmissionStatus.Draft,
                cancellationToken);

        PricingDraftDto? draft = null;

        if (draftSubmission != null)
        {
            var bidPricings = await _context.BidPricings
                .Where(bp => bp.BidSubmissionId == draftSubmission.Id)
                .AsNoTracking()
                .ToListAsync(cancellationToken);

            var entries = bidPricings.Select(bp => new PricingEntryDto
            {
                NodeId = bp.BoqSectionId ?? bp.BoqItemId ?? Guid.Empty,
                UnitRate = bp.NativeUnitRate,
                LumpSum = tender.PricingLevel == PricingLevel.Bill ? bp.NativeAmount : null,
                Amount = bp.NativeAmount
            }).ToList();

            var pricedCount = entries.Count(e => e.Amount.HasValue && e.Amount.Value != 0);
            var totalPriceable = priceableNodes.Count;

            draft = new PricingDraftDto
            {
                DraftId = draftSubmission.Id,
                LastSavedAt = draftSubmission.UpdatedAt ?? draftSubmission.CreatedAt,
                Entries = entries,
                GrandTotal = entries.Sum(e => e.Amount ?? 0),
                CompletionPercentage = totalPriceable > 0
                    ? (int)Math.Round(100.0 * pricedCount / totalPriceable)
                    : 0
            };
        }

        return new ContractorPricingViewDto
        {
            TenderId = request.TenderId,
            PricingLevel = tender.PricingLevel,
            Nodes = nodes,
            Draft = draft
        };
    }

    /// <summary>
    /// Builds the pricing tree from BOQ sections and items based on the pricing level.
    /// </summary>
    private static List<PricingNodeDto> BuildPricingTree(
        List<BoqSection> sections,
        PricingLevel pricingLevel,
        PriceableNodes priceableNodes)
    {
        // Get only top-level sections (bills)
        var topSections = sections
            .Where(s => s.ParentSectionId == null)
            .OrderBy(s => s.SortOrder)
            .ToList();

        // Build a lookup of all sections by ID for child section resolution
        var sectionLookup = sections.ToDictionary(s => s.Id);

        return pricingLevel switch
        {
            PricingLevel.Bill => BuildBillLevelTree(topSections, sectionLookup, priceableNodes),
            PricingLevel.Item => BuildItemLevelTree(topSections, sectionLookup, priceableNodes),
            PricingLevel.SubItem => BuildSubItemLevelTree(topSections, sectionLookup, priceableNodes),
            _ => new List<PricingNodeDto>()
        };
    }

    /// <summary>
    /// Bill-level: top-level sections are priceable (lump sum per bill).
    /// Items are shown as read-only context beneath each bill.
    /// </summary>
    private static List<PricingNodeDto> BuildBillLevelTree(
        List<BoqSection> topSections,
        Dictionary<Guid, BoqSection> sectionLookup,
        PriceableNodes priceableNodes)
    {
        var nodes = new List<PricingNodeDto>();

        foreach (var section in topSections)
        {
            var billNode = new PricingNodeDto
            {
                Id = section.Id,
                NodeType = "bill",
                Number = section.SectionNumber,
                Description = section.Title,
                IsPriceable = priceableNodes.SectionIds.Contains(section.Id),
                IsReadOnly = false,
                Children = BuildReadOnlyItemNodes(section, sectionLookup)
            };

            nodes.Add(billNode);
        }

        return nodes;
    }

    /// <summary>
    /// Item-level: top-level items are priceable. Sub-items shown as read-only.
    /// </summary>
    private static List<PricingNodeDto> BuildItemLevelTree(
        List<BoqSection> topSections,
        Dictionary<Guid, BoqSection> sectionLookup,
        PriceableNodes priceableNodes)
    {
        var nodes = new List<PricingNodeDto>();

        foreach (var section in topSections)
        {
            var billNode = new PricingNodeDto
            {
                Id = section.Id,
                NodeType = "bill",
                Number = section.SectionNumber,
                Description = section.Title,
                IsPriceable = false,
                IsReadOnly = true
            };

            // Add top-level items in this section as priceable children
            var topItems = GetAllItemsInSectionTree(section, sectionLookup)
                .Where(i => i.ParentItemId == null)
                .OrderBy(i => i.SortOrder);

            foreach (var item in topItems)
            {
                var itemNode = new PricingNodeDto
                {
                    Id = item.Id,
                    NodeType = "item",
                    Number = item.ItemNumber,
                    Description = item.Description,
                    Quantity = item.IsGroup ? null : item.Quantity,
                    Uom = item.IsGroup ? null : item.Uom,
                    IsPriceable = priceableNodes.ItemIds.Contains(item.Id),
                    IsReadOnly = false
                };

                // Sub-items shown as read-only context
                if (item.IsGroup && item.ChildItems.Any())
                {
                    itemNode.Children = item.ChildItems
                        .OrderBy(c => c.SortOrder)
                        .Select(c => new PricingNodeDto
                        {
                            Id = c.Id,
                            NodeType = "sub_item",
                            Number = c.ItemNumber,
                            Description = c.Description,
                            Quantity = c.Quantity,
                            Uom = c.Uom,
                            IsPriceable = false,
                            IsReadOnly = true
                        })
                        .ToList();
                }

                billNode.Children.Add(itemNode);
            }

            nodes.Add(billNode);
        }

        return nodes;
    }

    /// <summary>
    /// SubItem-level: all leaf (non-group) items are priceable.
    /// </summary>
    private static List<PricingNodeDto> BuildSubItemLevelTree(
        List<BoqSection> topSections,
        Dictionary<Guid, BoqSection> sectionLookup,
        PriceableNodes priceableNodes)
    {
        var nodes = new List<PricingNodeDto>();

        foreach (var section in topSections)
        {
            var billNode = new PricingNodeDto
            {
                Id = section.Id,
                NodeType = "bill",
                Number = section.SectionNumber,
                Description = section.Title,
                IsPriceable = false,
                IsReadOnly = true
            };

            // Add all items, with leaf items priceable
            var topItems = GetAllItemsInSectionTree(section, sectionLookup)
                .Where(i => i.ParentItemId == null)
                .OrderBy(i => i.SortOrder);

            foreach (var item in topItems)
            {
                billNode.Children.Add(BuildSubItemNode(item, priceableNodes));
            }

            nodes.Add(billNode);
        }

        return nodes;
    }

    /// <summary>
    /// Recursively builds a pricing node for sub-item level pricing.
    /// Group items are read-only containers; leaf items are priceable.
    /// </summary>
    private static PricingNodeDto BuildSubItemNode(BoqItem item, PriceableNodes priceableNodes)
    {
        var isPriceable = !item.IsGroup && priceableNodes.ItemIds.Contains(item.Id);

        var node = new PricingNodeDto
        {
            Id = item.Id,
            NodeType = item.ParentItemId == null ? "item" : "sub_item",
            Number = item.ItemNumber,
            Description = item.Description,
            Quantity = item.IsGroup ? null : item.Quantity,
            Uom = item.IsGroup ? null : item.Uom,
            IsPriceable = isPriceable,
            IsReadOnly = item.IsGroup
        };

        if (item.IsGroup && item.ChildItems.Any())
        {
            node.Children = item.ChildItems
                .OrderBy(c => c.SortOrder)
                .Select(c => BuildSubItemNode(c, priceableNodes))
                .ToList();
        }

        return node;
    }

    /// <summary>
    /// Builds read-only item nodes beneath a bill (used for bill-level pricing context).
    /// </summary>
    private static List<PricingNodeDto> BuildReadOnlyItemNodes(
        BoqSection section,
        Dictionary<Guid, BoqSection> sectionLookup)
    {
        var items = GetAllItemsInSectionTree(section, sectionLookup);
        return items
            .Where(i => i.ParentItemId == null)
            .OrderBy(i => i.SortOrder)
            .Select(i => BuildReadOnlyItemNode(i))
            .ToList();
    }

    /// <summary>
    /// Recursively builds a read-only item node.
    /// </summary>
    private static PricingNodeDto BuildReadOnlyItemNode(BoqItem item)
    {
        var node = new PricingNodeDto
        {
            Id = item.Id,
            NodeType = item.ParentItemId == null ? "item" : "sub_item",
            Number = item.ItemNumber,
            Description = item.Description,
            Quantity = item.IsGroup ? null : item.Quantity,
            Uom = item.IsGroup ? null : item.Uom,
            IsPriceable = false,
            IsReadOnly = true
        };

        if (item.IsGroup && item.ChildItems.Any())
        {
            node.Children = item.ChildItems
                .OrderBy(c => c.SortOrder)
                .Select(c => BuildReadOnlyItemNode(c))
                .ToList();
        }

        return node;
    }

    /// <summary>
    /// Collects all items across a section and its child sections recursively.
    /// </summary>
    private static List<BoqItem> GetAllItemsInSectionTree(
        BoqSection section,
        Dictionary<Guid, BoqSection> sectionLookup)
    {
        var items = new List<BoqItem>(section.Items);

        // Find child sections of this section
        var childSections = sectionLookup.Values
            .Where(s => s.ParentSectionId == section.Id)
            .OrderBy(s => s.SortOrder);

        foreach (var childSection in childSections)
        {
            items.AddRange(GetAllItemsInSectionTree(childSection, sectionLookup));
        }

        return items;
    }
}
