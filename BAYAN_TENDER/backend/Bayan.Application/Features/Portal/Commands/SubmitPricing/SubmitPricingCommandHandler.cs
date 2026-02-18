using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.Services;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Commands.SubmitPricing;

/// <summary>
/// Handler for SubmitPricingCommand.
/// Validates completeness, saves all entries, transitions to Submitted, and calculates grand total.
/// </summary>
public class SubmitPricingCommandHandler
    : IRequestHandler<SubmitPricingCommand, SubmitPricingResult>
{
    private readonly IApplicationDbContext _context;
    private readonly IBoqRollUpService _rollUpService;

    public SubmitPricingCommandHandler(
        IApplicationDbContext context,
        IBoqRollUpService rollUpService)
    {
        _context = context;
        _rollUpService = rollUpService;
    }

    public async Task<SubmitPricingResult> Handle(
        SubmitPricingCommand request,
        CancellationToken cancellationToken)
    {
        // 1. Validate tender exists and is active
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken)
            ?? throw new KeyNotFoundException($"Tender {request.TenderId} not found.");

        if (tender.Status != TenderStatus.Active)
        {
            throw new InvalidOperationException("Bids can only be submitted for active tenders.");
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

        // 3. Check for existing submitted bid (prevent duplicate submissions)
        var existingSubmitted = await _context.BidSubmissions
            .AsNoTracking()
            .AnyAsync(
                bs => bs.TenderId == request.TenderId
                    && bs.BidderId == request.BidderId
                    && bs.Status == BidSubmissionStatus.Submitted,
                cancellationToken);

        if (existingSubmitted)
        {
            throw new InvalidOperationException("You have already submitted a bid for this tender.");
        }

        // 4. Get priceable nodes
        var priceableNodes = await _rollUpService.GetPriceableNodeIdsAsync(
            request.TenderId, cancellationToken);

        // 5. Find or create BidSubmission (may already exist as Draft)
        var submission = await _context.BidSubmissions
            .FirstOrDefaultAsync(
                bs => bs.TenderId == request.TenderId
                    && bs.BidderId == request.BidderId
                    && bs.Status == BidSubmissionStatus.Draft,
                cancellationToken);

        if (submission == null)
        {
            submission = new BidSubmission
            {
                Id = Guid.NewGuid(),
                TenderId = request.TenderId,
                BidderId = request.BidderId,
                NativeCurrency = tender.BaseCurrency,
                CreatedAt = DateTime.UtcNow
            };
            _context.BidSubmissions.Add(submission);
        }

        // 6. Load items for quantity lookup
        var itemQuantities = await _context.BoqItems
            .Where(i => i.TenderId == request.TenderId)
            .AsNoTracking()
            .ToDictionaryAsync(i => i.Id, i => i.Quantity, cancellationToken);

        // 7. Clear existing pricing rows and save new ones
        var existingPricings = await _context.BidPricings
            .Where(bp => bp.BidSubmissionId == submission.Id)
            .ToListAsync(cancellationToken);

        // Remove old rows
        foreach (var old in existingPricings)
        {
            _context.BidPricings.Remove(old);
        }

        // Save all new entries
        foreach (var entry in request.Entries)
        {
            var isBillPricing = priceableNodes.SectionIds.Contains(entry.NodeId);
            var isItemPricing = priceableNodes.ItemIds.Contains(entry.NodeId);

            if (!isBillPricing && !isItemPricing)
            {
                continue;
            }

            var pricing = new BidPricing
            {
                Id = Guid.NewGuid(),
                BidSubmissionId = submission.Id,
                NativeCurrency = tender.BaseCurrency,
                IsIncludedInTotal = true,
                FxRateApplied = 1.0m,
                CreatedAt = DateTime.UtcNow
            };

            if (isBillPricing)
            {
                pricing.BoqSectionId = entry.NodeId;
                pricing.NativeAmount = entry.LumpSum ?? entry.Amount;
                pricing.NativeUnitRate = null;
            }
            else
            {
                pricing.BoqItemId = entry.NodeId;
                pricing.NativeUnitRate = entry.UnitRate;
                var quantity = itemQuantities.GetValueOrDefault(entry.NodeId, 0);
                pricing.NativeAmount = entry.UnitRate.HasValue
                    ? entry.UnitRate.Value * quantity
                    : entry.Amount;
            }

            pricing.NormalizedUnitRate = pricing.NativeUnitRate;
            pricing.NormalizedAmount = pricing.NativeAmount;

            _context.BidPricings.Add(pricing);
        }

        // 8. Validate completeness — all priceable nodes must have a pricing entry
        var pricedNodeIds = request.Entries
            .Where(e =>
                priceableNodes.SectionIds.Contains(e.NodeId) ||
                priceableNodes.ItemIds.Contains(e.NodeId))
            .Where(e => (e.Amount ?? e.LumpSum ?? e.UnitRate) != null
                && (e.Amount ?? e.LumpSum ?? e.UnitRate) != 0)
            .Select(e => e.NodeId)
            .ToHashSet();

        var allPriceableIds = priceableNodes.SectionIds
            .Concat(priceableNodes.ItemIds)
            .ToList();

        var missingNodes = allPriceableIds
            .Where(id => !pricedNodeIds.Contains(id))
            .ToList();

        if (missingNodes.Any())
        {
            throw new InvalidOperationException(
                $"All priceable items must have pricing before submission. {missingNodes.Count} item(s) are missing pricing.");
        }

        // 9. Transition to Submitted
        var now = DateTime.UtcNow;
        submission.Status = BidSubmissionStatus.Submitted;
        submission.SubmissionTime = now;
        submission.UpdatedAt = now;
        submission.BidValidityDays = tender.BidValidityDays;
        submission.ReceiptNumber = GenerateReceiptNumber(tender.Reference);

        await _context.SaveChangesAsync(cancellationToken);

        // 10. Calculate grand total via roll-up service
        var grandTotal = await _rollUpService.CalculateGrandTotalAsync(
            request.TenderId, submission.Id, cancellationToken);

        // Update totals on submission
        submission.NativeTotalAmount = grandTotal;
        submission.NormalizedTotalAmount = grandTotal;
        await _context.SaveChangesAsync(cancellationToken);

        return new SubmitPricingResult
        {
            SubmissionId = submission.Id,
            GrandTotal = grandTotal,
            SubmittedAt = now,
            ReceiptNumber = submission.ReceiptNumber
        };
    }

    /// <summary>
    /// Generates a receipt number from the tender reference and timestamp.
    /// Format: {TenderRef}-{yyyyMMddHHmmss}
    /// </summary>
    private static string GenerateReceiptNumber(string tenderReference)
    {
        var timestamp = DateTime.UtcNow.ToString("yyyyMMddHHmmss");
        var cleanRef = tenderReference.Replace(" ", "").Replace("/", "-");
        return $"{cleanRef}-{timestamp}";
    }
}
