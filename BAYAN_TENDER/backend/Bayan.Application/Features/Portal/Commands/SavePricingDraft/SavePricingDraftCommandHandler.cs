using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.Services;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Commands.SavePricingDraft;

/// <summary>
/// Handler for SavePricingDraftCommand.
/// Creates or updates a draft BidSubmission with BidPricing rows.
/// </summary>
public class SavePricingDraftCommandHandler
    : IRequestHandler<SavePricingDraftCommand, SavePricingDraftResult>
{
    private readonly IApplicationDbContext _context;
    private readonly IBoqRollUpService _rollUpService;

    public SavePricingDraftCommandHandler(
        IApplicationDbContext context,
        IBoqRollUpService rollUpService)
    {
        _context = context;
        _rollUpService = rollUpService;
    }

    public async Task<SavePricingDraftResult> Handle(
        SavePricingDraftCommand request,
        CancellationToken cancellationToken)
    {
        // 1. Validate tender exists and is active
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken)
            ?? throw new KeyNotFoundException($"Tender {request.TenderId} not found.");

        if (tender.Status != TenderStatus.Active)
        {
            throw new InvalidOperationException("Pricing can only be saved for active tenders.");
        }

        if (DateTime.UtcNow > tender.SubmissionDeadline)
        {
            throw new InvalidOperationException("The submission deadline has passed.");
        }

        // 2. Validate bidder access
        var tenderBidder = await _context.TenderBidders
            .AsNoTracking()
            .FirstOrDefaultAsync(
                tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId,
                cancellationToken);

        if (tenderBidder == null || tenderBidder.QualificationStatus == QualificationStatus.Removed)
        {
            throw new UnauthorizedAccessException("You do not have access to this tender.");
        }

        // 3. Find or create draft BidSubmission
        var draftSubmission = await _context.BidSubmissions
            .FirstOrDefaultAsync(
                bs => bs.TenderId == request.TenderId
                    && bs.BidderId == request.BidderId
                    && bs.Status == BidSubmissionStatus.Draft,
                cancellationToken);

        if (draftSubmission == null)
        {
            draftSubmission = new BidSubmission
            {
                Id = Guid.NewGuid(),
                TenderId = request.TenderId,
                BidderId = request.BidderId,
                Status = BidSubmissionStatus.Draft,
                NativeCurrency = tender.BaseCurrency,
                SubmissionTime = DateTime.UtcNow,
                CreatedAt = DateTime.UtcNow
            };
            _context.BidSubmissions.Add(draftSubmission);
        }

        draftSubmission.UpdatedAt = DateTime.UtcNow;

        // 4. Get priceable nodes for validation
        var priceableNodes = await _rollUpService.GetPriceableNodeIdsAsync(
            request.TenderId, cancellationToken);

        // 5. Load existing BidPricing rows for this draft
        var existingPricings = await _context.BidPricings
            .Where(bp => bp.BidSubmissionId == draftSubmission.Id)
            .ToListAsync(cancellationToken);

        // 6. Load items for quantity lookup (needed for Amount = UnitRate * Quantity)
        var itemQuantities = await _context.BoqItems
            .Where(i => i.TenderId == request.TenderId)
            .AsNoTracking()
            .ToDictionaryAsync(i => i.Id, i => i.Quantity, cancellationToken);

        // 7. Upsert BidPricing rows
        foreach (var entry in request.Entries)
        {
            // Determine if this node is a section (bill) or item
            var isBillPricing = priceableNodes.SectionIds.Contains(entry.NodeId);
            var isItemPricing = priceableNodes.ItemIds.Contains(entry.NodeId);

            if (!isBillPricing && !isItemPricing)
            {
                // Skip entries for non-priceable nodes
                continue;
            }

            // Find existing pricing row
            var existing = existingPricings.FirstOrDefault(bp =>
                (isBillPricing && bp.BoqSectionId == entry.NodeId) ||
                (isItemPricing && bp.BoqItemId == entry.NodeId));

            if (existing != null)
            {
                // Update existing
                if (isBillPricing)
                {
                    existing.NativeAmount = entry.LumpSum ?? entry.Amount;
                    existing.NativeUnitRate = null;
                }
                else
                {
                    existing.NativeUnitRate = entry.UnitRate;
                    var quantity = itemQuantities.GetValueOrDefault(entry.NodeId, 0);
                    existing.NativeAmount = entry.UnitRate.HasValue
                        ? entry.UnitRate.Value * quantity
                        : entry.Amount;
                }

                // Also set normalized amounts (same as native for now, FX = 1)
                existing.NormalizedUnitRate = existing.NativeUnitRate;
                existing.NormalizedAmount = existing.NativeAmount;
                existing.UpdatedAt = DateTime.UtcNow;
            }
            else
            {
                // Create new pricing row
                var newPricing = new BidPricing
                {
                    Id = Guid.NewGuid(),
                    BidSubmissionId = draftSubmission.Id,
                    NativeCurrency = tender.BaseCurrency,
                    IsIncludedInTotal = true,
                    CreatedAt = DateTime.UtcNow
                };

                if (isBillPricing)
                {
                    newPricing.BoqSectionId = entry.NodeId;
                    newPricing.NativeAmount = entry.LumpSum ?? entry.Amount;
                    newPricing.NativeUnitRate = null;
                }
                else
                {
                    newPricing.BoqItemId = entry.NodeId;
                    newPricing.NativeUnitRate = entry.UnitRate;
                    var quantity = itemQuantities.GetValueOrDefault(entry.NodeId, 0);
                    newPricing.NativeAmount = entry.UnitRate.HasValue
                        ? entry.UnitRate.Value * quantity
                        : entry.Amount;
                }

                newPricing.NormalizedUnitRate = newPricing.NativeUnitRate;
                newPricing.NormalizedAmount = newPricing.NativeAmount;
                newPricing.FxRateApplied = 1.0m;

                _context.BidPricings.Add(newPricing);
            }
        }

        await _context.SaveChangesAsync(cancellationToken);

        // 8. Calculate totals for response
        var allPricings = await _context.BidPricings
            .Where(bp => bp.BidSubmissionId == draftSubmission.Id)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        var grandTotal = allPricings.Sum(bp => bp.NativeAmount ?? 0);
        var pricedCount = allPricings.Count(bp => bp.NativeAmount.HasValue && bp.NativeAmount.Value != 0);
        var totalPriceable = priceableNodes.Count;

        // Update submission total
        draftSubmission.NativeTotalAmount = grandTotal;
        draftSubmission.NormalizedTotalAmount = grandTotal;
        await _context.SaveChangesAsync(cancellationToken);

        return new SavePricingDraftResult
        {
            DraftId = draftSubmission.Id,
            SavedAt = draftSubmission.UpdatedAt ?? DateTime.UtcNow,
            GrandTotal = grandTotal,
            CompletionPercentage = totalPriceable > 0
                ? (int)Math.Round(100.0 * pricedCount / totalPriceable)
                : 0
        };
    }
}
