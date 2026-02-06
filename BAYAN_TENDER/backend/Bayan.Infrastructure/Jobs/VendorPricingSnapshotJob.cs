using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Jobs;

/// <summary>
/// Background job to create vendor pricing snapshots after bid import.
/// Triggered when bids are successfully imported to capture pricing data.
/// </summary>
public class VendorPricingSnapshotJob
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<VendorPricingSnapshotJob> _logger;

    public VendorPricingSnapshotJob(
        IApplicationDbContext context,
        ILogger<VendorPricingSnapshotJob> logger)
    {
        _context = context;
        _logger = logger;
    }

    /// <summary>
    /// Creates a vendor pricing snapshot for a specific bid submission.
    /// </summary>
    /// <param name="bidSubmissionId">The bid submission ID.</param>
    public async Task ExecuteAsync(Guid bidSubmissionId)
    {
        _logger.LogInformation(
            "Starting vendor pricing snapshot job for bid submission {BidSubmissionId}",
            bidSubmissionId);

        try
        {
            // Get the bid submission with related data
            var bidSubmission = await _context.BidSubmissions
                .AsNoTracking()
                .Include(bs => bs.Bidder)
                .Include(bs => bs.Tender)
                .FirstOrDefaultAsync(bs => bs.Id == bidSubmissionId);

            if (bidSubmission == null)
            {
                _logger.LogWarning(
                    "Bid submission {BidSubmissionId} not found",
                    bidSubmissionId);
                return;
            }

            // Check if snapshot already exists
            var existingSnapshot = await _context.VendorPricingSnapshots
                .AsNoTracking()
                .AnyAsync(s => s.BidSubmissionId == bidSubmissionId);

            if (existingSnapshot)
            {
                _logger.LogInformation(
                    "Snapshot already exists for bid submission {BidSubmissionId}",
                    bidSubmissionId);
                return;
            }

            // Get bid pricing items
            var bidPricings = await _context.BidPricings
                .AsNoTracking()
                .Include(bp => bp.BoqItem)
                .Where(bp => bp.BidSubmissionId == bidSubmissionId)
                .ToListAsync();

            if (!bidPricings.Any())
            {
                _logger.LogWarning(
                    "No pricing data found for bid submission {BidSubmissionId}",
                    bidSubmissionId);
                return;
            }

            // Create the snapshot
            var snapshot = new VendorPricingSnapshot
            {
                Id = Guid.NewGuid(),
                BidderId = bidSubmission.BidderId,
                TenderId = bidSubmission.TenderId,
                BidSubmissionId = bidSubmissionId,
                SnapshotDate = DateTime.UtcNow,
                TenderBaseCurrency = bidSubmission.Tender?.BaseCurrency ?? "AED",
                TotalBidAmount = bidPricings.Sum(bp => bp.NativeAmount ?? 0),
                TotalItemsCount = bidPricings.Count,
                CreatedAt = DateTime.UtcNow
            };

            _context.VendorPricingSnapshots.Add(snapshot);

            // Create item rates
            foreach (var pricing in bidPricings)
            {
                var itemRate = new VendorItemRate
                {
                    Id = Guid.NewGuid(),
                    SnapshotId = snapshot.Id,
                    BoqItemId = pricing.BoqItemId,
                    ItemDescription = pricing.BoqItem?.Description ?? "Unknown Item",
                    Uom = pricing.BoqItem?.Uom ?? "N/A",
                    NormalizedUnitRate = pricing.NormalizedUnitRate ?? 0,
                    NormalizedCurrency = bidSubmission.Tender?.BaseCurrency ?? "AED",
                    Quantity = pricing.BidderQuantity,
                    TotalAmount = pricing.NativeAmount,
                    CreatedAt = DateTime.UtcNow
                };

                _context.VendorItemRates.Add(itemRate);
            }

            await _context.SaveChangesAsync();

            _logger.LogInformation(
                "Created vendor pricing snapshot {SnapshotId} with {ItemCount} items for bidder {BidderName}",
                snapshot.Id,
                bidPricings.Count,
                bidSubmission.Bidder?.CompanyName ?? "Unknown");
        }
        catch (Exception ex)
        {
            _logger.LogError(
                ex,
                "Error creating vendor pricing snapshot for bid submission {BidSubmissionId}",
                bidSubmissionId);
            throw;
        }
    }

    /// <summary>
    /// Creates vendor pricing snapshots for all bid submissions in a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    public async Task ExecuteForTenderAsync(Guid tenderId)
    {
        _logger.LogInformation(
            "Starting vendor pricing snapshot job for tender {TenderId}",
            tenderId);

        try
        {
            var bidSubmissions = await _context.BidSubmissions
                .AsNoTracking()
                .Where(bs => bs.TenderId == tenderId)
                .Select(bs => bs.Id)
                .ToListAsync();

            _logger.LogInformation(
                "Found {Count} bid submissions for tender {TenderId}",
                bidSubmissions.Count,
                tenderId);

            var created = 0;
            var skipped = 0;
            var errors = 0;

            foreach (var bidSubmissionId in bidSubmissions)
            {
                try
                {
                    // Check if snapshot already exists
                    var existingSnapshot = await _context.VendorPricingSnapshots
                        .AsNoTracking()
                        .AnyAsync(s => s.BidSubmissionId == bidSubmissionId);

                    if (existingSnapshot)
                    {
                        skipped++;
                        continue;
                    }

                    await ExecuteAsync(bidSubmissionId);
                    created++;
                }
                catch (Exception ex)
                {
                    errors++;
                    _logger.LogError(
                        ex,
                        "Error creating snapshot for bid submission {BidSubmissionId}",
                        bidSubmissionId);
                }
            }

            _logger.LogInformation(
                "Vendor pricing snapshot job for tender {TenderId} completed. Created: {Created}, Skipped: {Skipped}, Errors: {Errors}",
                tenderId,
                created,
                skipped,
                errors);
        }
        catch (Exception ex)
        {
            _logger.LogError(
                ex,
                "Error executing vendor pricing snapshot job for tender {TenderId}",
                tenderId);
            throw;
        }
    }
}
