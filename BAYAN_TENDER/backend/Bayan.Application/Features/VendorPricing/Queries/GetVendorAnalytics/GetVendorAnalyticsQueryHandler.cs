using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorAnalytics;

/// <summary>
/// Handler for GetVendorAnalyticsQuery.
/// </summary>
public class GetVendorAnalyticsQueryHandler
    : IRequestHandler<GetVendorAnalyticsQuery, VendorAnalyticsDto?>
{
    private readonly IApplicationDbContext _context;

    public GetVendorAnalyticsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<VendorAnalyticsDto?> Handle(
        GetVendorAnalyticsQuery request,
        CancellationToken cancellationToken)
    {
        // Get bidder info
        var bidder = await _context.Bidders
            .AsNoTracking()
            .FirstOrDefaultAsync(b => b.Id == request.BidderId, cancellationToken);

        if (bidder == null)
        {
            return null;
        }

        // Build query for snapshots
        var snapshotsQuery = _context.VendorPricingSnapshots
            .AsNoTracking()
            .Include(s => s.Tender)
            .Where(s => s.BidderId == request.BidderId);

        if (request.FromDate.HasValue)
        {
            snapshotsQuery = snapshotsQuery.Where(s => s.SnapshotDate >= request.FromDate.Value);
        }

        if (request.ToDate.HasValue)
        {
            snapshotsQuery = snapshotsQuery.Where(s => s.SnapshotDate <= request.ToDate.Value);
        }

        var snapshots = await snapshotsQuery.ToListAsync(cancellationToken);

        // Build query for item rates
        var ratesQuery = _context.VendorItemRates
            .AsNoTracking()
            .Include(r => r.Snapshot)
            .Where(r => r.Snapshot.BidderId == request.BidderId);

        if (request.FromDate.HasValue)
        {
            ratesQuery = ratesQuery.Where(r => r.Snapshot.SnapshotDate >= request.FromDate.Value);
        }

        if (request.ToDate.HasValue)
        {
            ratesQuery = ratesQuery.Where(r => r.Snapshot.SnapshotDate <= request.ToDate.Value);
        }

        var rates = await ratesQuery.ToListAsync(cancellationToken);

        // Build analytics DTO
        var analytics = new VendorAnalyticsDto
        {
            BidderId = request.BidderId,
            BidderName = bidder.CompanyName,
            TotalSnapshots = snapshots.Count,
            TotalUniqueItems = rates
                .Select(r => new { r.ItemDescription, r.Uom })
                .Distinct()
                .Count()
        };

        if (snapshots.Any())
        {
            var orderedSnapshots = snapshots.OrderBy(s => s.SnapshotDate).ToList();
            analytics.FirstSnapshotDate = orderedSnapshots.First().SnapshotDate;
            analytics.LastSnapshotDate = orderedSnapshots.Last().SnapshotDate;
            analytics.AverageBidAmount = snapshots.Average(s => s.TotalBidAmount);

            // Calculate overall trend based on bid amounts
            if (orderedSnapshots.Count >= 2)
            {
                var firstAmount = orderedSnapshots.First().TotalBidAmount;
                var lastAmount = orderedSnapshots.Last().TotalBidAmount;

                if (firstAmount != 0)
                {
                    var percentChange = ((lastAmount - firstAmount) / firstAmount) * 100;
                    analytics.OverallTrendDirection = percentChange switch
                    {
                        > 5 => "up",
                        < -5 => "down",
                        _ => "stable"
                    };
                }
            }
            else
            {
                analytics.OverallTrendDirection = "stable";
            }
        }

        // Calculate per-item analytics
        var itemGroups = rates
            .GroupBy(r => new { r.ItemDescription, r.Uom })
            .Take(request.MaxItemAnalytics)
            .ToList();

        var itemAnalyticsList = new List<VendorItemAnalyticsDto>();
        var volatilities = new List<decimal>();

        foreach (var group in itemGroups)
        {
            var orderedRates = group.OrderBy(r => r.Snapshot.SnapshotDate).ToList();
            var rateValues = orderedRates.Select(r => r.NormalizedUnitRate).ToList();

            if (!rateValues.Any())
                continue;

            var itemAnalytics = new VendorItemAnalyticsDto
            {
                ItemDescription = group.Key.ItemDescription,
                Uom = group.Key.Uom,
                DataPointCount = rateValues.Count,
                AverageRate = rateValues.Average(),
                MinRate = rateValues.Min(),
                MaxRate = rateValues.Max(),
                LatestRate = rateValues.Last()
            };

            // Calculate standard deviation
            if (rateValues.Count > 1)
            {
                var mean = itemAnalytics.AverageRate;
                var sumOfSquares = rateValues.Sum(r => (r - mean) * (r - mean));
                itemAnalytics.StandardDeviation = (decimal)Math.Sqrt((double)(sumOfSquares / rateValues.Count));

                // Calculate volatility (coefficient of variation)
                if (mean != 0)
                {
                    itemAnalytics.Volatility = (itemAnalytics.StandardDeviation / mean) * 100;
                    volatilities.Add(itemAnalytics.Volatility);
                }
            }

            // Calculate trend
            if (rateValues.Count >= 2)
            {
                var firstRate = rateValues.First();
                var lastRate = rateValues.Last();

                if (firstRate != 0)
                {
                    itemAnalytics.PercentageChange = ((lastRate - firstRate) / firstRate) * 100;
                }

                itemAnalytics.TrendDirection = itemAnalytics.PercentageChange switch
                {
                    > 5 => "up",
                    < -5 => "down",
                    _ => "stable"
                };
            }
            else
            {
                itemAnalytics.TrendDirection = "stable";
            }

            itemAnalyticsList.Add(itemAnalytics);
        }

        analytics.ItemAnalytics = itemAnalyticsList;

        // Calculate average volatility
        if (volatilities.Any())
        {
            analytics.AverageVolatility = volatilities.Average();
        }

        // Add tender summaries if requested
        if (request.IncludeTenderSummaries)
        {
            analytics.TenderSummaries = snapshots
                .OrderByDescending(s => s.SnapshotDate)
                .Select(s => new VendorTenderSummaryDto
                {
                    TenderId = s.TenderId,
                    TenderReference = s.Tender?.Reference ?? "Unknown",
                    TenderTitle = s.Tender?.Title ?? "Unknown",
                    SnapshotDate = s.SnapshotDate,
                    TotalBidAmount = s.TotalBidAmount,
                    ItemCount = s.TotalItemsCount,
                    Currency = s.TenderBaseCurrency
                })
                .ToList();
        }

        return analytics;
    }
}
