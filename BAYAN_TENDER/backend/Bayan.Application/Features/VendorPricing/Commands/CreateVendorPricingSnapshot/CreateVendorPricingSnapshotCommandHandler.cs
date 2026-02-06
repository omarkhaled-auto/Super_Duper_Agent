using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.VendorPricing.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.VendorPricing.Commands.CreateVendorPricingSnapshot;

/// <summary>
/// Handler for CreateVendorPricingSnapshotCommand.
/// Creates vendor pricing snapshots and item rates from bid pricing data.
/// </summary>
public class CreateVendorPricingSnapshotCommandHandler
    : IRequestHandler<CreateVendorPricingSnapshotCommand, VendorPricingSnapshotDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<CreateVendorPricingSnapshotCommandHandler> _logger;

    public CreateVendorPricingSnapshotCommandHandler(
        IApplicationDbContext context,
        ILogger<CreateVendorPricingSnapshotCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<VendorPricingSnapshotDto> Handle(
        CreateVendorPricingSnapshotCommand request,
        CancellationToken cancellationToken)
    {
        // Fetch the bid submission with related data
        var bidSubmission = await _context.BidSubmissions
            .AsNoTracking()
            .Include(bs => bs.Bidder)
            .Include(bs => bs.Tender)
            .FirstOrDefaultAsync(bs => bs.Id == request.BidSubmissionId, cancellationToken);

        if (bidSubmission == null)
        {
            throw new InvalidOperationException($"Bid submission with ID {request.BidSubmissionId} not found.");
        }

        // Check if a snapshot already exists for this bid submission
        var existingSnapshot = await _context.VendorPricingSnapshots
            .AsNoTracking()
            .FirstOrDefaultAsync(s => s.BidSubmissionId == request.BidSubmissionId, cancellationToken);

        if (existingSnapshot != null)
        {
            _logger.LogWarning(
                "Vendor pricing snapshot already exists for bid submission {BidSubmissionId}. Returning existing snapshot.",
                request.BidSubmissionId);

            return MapToDto(existingSnapshot, bidSubmission);
        }

        // Fetch bid pricing data
        var bidPricings = await _context.BidPricings
            .AsNoTracking()
            .Where(bp => bp.BidSubmissionId == request.BidSubmissionId)
            .Include(bp => bp.BoqItem)
            .ToListAsync(cancellationToken);

        if (!bidPricings.Any())
        {
            _logger.LogWarning(
                "No bid pricing data found for bid submission {BidSubmissionId}.",
                request.BidSubmissionId);
        }

        // Create the snapshot
        var snapshotDate = request.SnapshotDate ?? DateTime.UtcNow;
        var snapshot = new VendorPricingSnapshot
        {
            Id = Guid.NewGuid(),
            BidderId = bidSubmission.BidderId,
            TenderId = bidSubmission.TenderId,
            BidSubmissionId = bidSubmission.Id,
            SnapshotDate = snapshotDate,
            TenderBaseCurrency = bidSubmission.Tender.BaseCurrency,
            TotalBidAmount = bidSubmission.NativeTotalAmount ?? 0,
            TotalItemsCount = bidPricings.Count,
            CreatedAt = DateTime.UtcNow
        };

        _context.VendorPricingSnapshots.Add(snapshot);

        // Create vendor item rates from bid pricing
        var itemRates = new List<VendorItemRate>();
        foreach (var pricing in bidPricings)
        {
            // Skip items without valid rates
            if (!pricing.NormalizedUnitRate.HasValue || pricing.NormalizedUnitRate.Value == 0)
            {
                continue;
            }

            var itemRate = new VendorItemRate
            {
                Id = Guid.NewGuid(),
                SnapshotId = snapshot.Id,
                BoqItemId = pricing.BoqItemId,
                ItemDescription = pricing.BidderDescription ?? pricing.BoqItem?.Description ?? "Unknown Item",
                Uom = pricing.BidderUom ?? pricing.BoqItem?.Uom ?? "N/A",
                NormalizedUnitRate = pricing.NormalizedUnitRate.Value,
                NormalizedCurrency = bidSubmission.Tender.BaseCurrency,
                Quantity = pricing.BidderQuantity,
                TotalAmount = pricing.NormalizedAmount,
                CreatedAt = DateTime.UtcNow
            };

            itemRates.Add(itemRate);
        }

        if (itemRates.Any())
        {
            _context.VendorItemRates.AddRange(itemRates);
            snapshot.TotalItemsCount = itemRates.Count;
        }

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Created vendor pricing snapshot {SnapshotId} for bidder {BidderId} with {ItemCount} items.",
            snapshot.Id, snapshot.BidderId, itemRates.Count);

        return MapToDto(snapshot, bidSubmission);
    }

    private static VendorPricingSnapshotDto MapToDto(VendorPricingSnapshot snapshot, BidSubmission bidSubmission)
    {
        return new VendorPricingSnapshotDto
        {
            Id = snapshot.Id,
            BidderId = snapshot.BidderId,
            BidderName = bidSubmission.Bidder?.CompanyName ?? "Unknown",
            TenderId = snapshot.TenderId,
            TenderReference = bidSubmission.Tender?.Reference ?? "Unknown",
            TenderTitle = bidSubmission.Tender?.Title ?? "Unknown",
            SnapshotDate = snapshot.SnapshotDate,
            ItemCount = snapshot.TotalItemsCount,
            TotalBidAmount = snapshot.TotalBidAmount,
            Currency = snapshot.TenderBaseCurrency
        };
    }
}
