using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Commands.UpdateOutlierStatus;

/// <summary>
/// Handler for UpdateOutlierStatusCommand.
/// Calculates outlier status for all bid pricing items in a tender.
/// </summary>
public class UpdateOutlierStatusCommandHandler : IRequestHandler<UpdateOutlierStatusCommand, OutlierRecalculationResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<UpdateOutlierStatusCommandHandler> _logger;

    public UpdateOutlierStatusCommandHandler(
        IApplicationDbContext context,
        ILogger<UpdateOutlierStatusCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<OutlierRecalculationResultDto> Handle(
        UpdateOutlierStatusCommand request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Starting outlier detection for tender {TenderId}", request.TenderId);

        // Verify tender exists
        var tenderExists = await _context.Tenders
            .AnyAsync(t => t.Id == request.TenderId, cancellationToken);

        if (!tenderExists)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Get all imported bid submissions for this tender
        var bidSubmissions = await _context.BidSubmissions
            .Where(bs => bs.TenderId == request.TenderId)
            .Where(bs => bs.ImportStatus == BidImportStatus.Imported)
            .Where(bs => bs.Status != BidSubmissionStatus.Disqualified)
            .Select(bs => bs.Id)
            .ToListAsync(cancellationToken);

        if (!bidSubmissions.Any())
        {
            _logger.LogWarning("No imported bids found for tender {TenderId}", request.TenderId);
            return new OutlierRecalculationResultDto
            {
                ItemsProcessed = 0,
                OutliersDetected = 0
            };
        }

        // Get all BOQ items for this tender
        var boqItemIds = await _context.BoqItems
            .Where(bi => bi.TenderId == request.TenderId)
            .Select(bi => bi.Id)
            .ToListAsync(cancellationToken);

        // Get all bid pricing for this tender (grouped by BOQ item)
        var allPricing = await _context.BidPricings
            .Where(bp => bidSubmissions.Contains(bp.BidSubmissionId))
            .Where(bp => bp.BoqItemId != null)
            .ToListAsync(cancellationToken);

        var result = new OutlierRecalculationResultDto
        {
            CalculatedAt = DateTime.UtcNow
        };

        // Group pricing by BOQ item
        var pricingByItem = allPricing.GroupBy(p => p.BoqItemId!.Value);

        foreach (var itemGroup in pricingByItem)
        {
            result.ItemsProcessed++;

            // Get valid rates (exclude NoBid and NonComparable)
            var validRates = itemGroup
                .Where(p => !p.IsNoBid && !p.IsNonComparable && p.NormalizedUnitRate.HasValue)
                .ToList();

            if (validRates.Count < 2)
            {
                // Not enough rates to calculate outliers
                foreach (var pricing in itemGroup)
                {
                    pricing.IsOutlier = false;
                    pricing.OutlierSeverity = null;
                    pricing.DeviationFromAverage = null;
                }
                continue;
            }

            // Calculate average
            var average = validRates.Average(p => p.NormalizedUnitRate!.Value);

            if (average == 0)
            {
                // Cannot calculate deviation from zero
                continue;
            }

            // Calculate deviation for each rate
            foreach (var pricing in itemGroup)
            {
                if (pricing.IsNoBid || pricing.IsNonComparable || !pricing.NormalizedUnitRate.HasValue)
                {
                    pricing.IsOutlier = false;
                    pricing.OutlierSeverity = null;
                    pricing.DeviationFromAverage = null;
                    continue;
                }

                var rate = pricing.NormalizedUnitRate.Value;
                var deviationPct = Math.Abs((rate - average) / average) * 100;

                pricing.DeviationFromAverage = Math.Round(deviationPct, 2);

                // Determine severity
                if (deviationPct > request.HighThreshold)
                {
                    pricing.IsOutlier = true;
                    pricing.OutlierSeverity = OutlierSeverity.High;
                    result.HighSeverityCount++;
                    result.OutliersDetected++;
                }
                else if (deviationPct > request.MediumThreshold)
                {
                    pricing.IsOutlier = true;
                    pricing.OutlierSeverity = OutlierSeverity.Medium;
                    result.MediumSeverityCount++;
                    result.OutliersDetected++;
                }
                else
                {
                    pricing.IsOutlier = false;
                    pricing.OutlierSeverity = OutlierSeverity.Low;
                    result.LowSeverityCount++;
                }
            }
        }

        // Save changes
        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Outlier detection completed for tender {TenderId}: {ItemsProcessed} items processed, " +
            "{OutliersDetected} outliers detected (High: {High}, Medium: {Medium}, Low: {Low})",
            request.TenderId,
            result.ItemsProcessed,
            result.OutliersDetected,
            result.HighSeverityCount,
            result.MediumSeverityCount,
            result.LowSeverityCount);

        return result;
    }
}
