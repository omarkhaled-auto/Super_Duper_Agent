using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorTrends;

/// <summary>
/// Handler for GetVendorTrendsQuery.
/// </summary>
public class GetVendorTrendsQueryHandler
    : IRequestHandler<GetVendorTrendsQuery, VendorTrendsDto?>
{
    private readonly IApplicationDbContext _context;

    public GetVendorTrendsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<VendorTrendsDto?> Handle(
        GetVendorTrendsQuery request,
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
            .Include(s => s.ItemRates)
            .Where(s => s.BidderId == request.BidderId);

        if (request.FromDate.HasValue)
        {
            snapshotsQuery = snapshotsQuery.Where(s => s.SnapshotDate >= request.FromDate.Value);
        }

        if (request.ToDate.HasValue)
        {
            snapshotsQuery = snapshotsQuery.Where(s => s.SnapshotDate <= request.ToDate.Value);
        }

        var snapshots = await snapshotsQuery
            .OrderBy(s => s.SnapshotDate)
            .ToListAsync(cancellationToken);

        if (!snapshots.Any())
        {
            return new VendorTrendsDto
            {
                BidderId = request.BidderId,
                BidderName = bidder.CompanyName,
                TradeSpecialization = bidder.TradeSpecialization,
                FromDate = request.FromDate,
                ToDate = request.ToDate
            };
        }

        var trends = new VendorTrendsDto
        {
            BidderId = request.BidderId,
            BidderName = bidder.CompanyName,
            TradeSpecialization = bidder.TradeSpecialization,
            FromDate = request.FromDate ?? snapshots.First().SnapshotDate,
            ToDate = request.ToDate ?? snapshots.Last().SnapshotDate
        };

        // Calculate summary statistics
        var allRates = snapshots.SelectMany(s => s.ItemRates).ToList();
        var totalBidValue = snapshots.Sum(s => s.TotalBidAmount);

        decimal overallPercentageChange = 0;
        if (snapshots.Count >= 2)
        {
            var first = snapshots.First().TotalBidAmount;
            var last = snapshots.Last().TotalBidAmount;
            if (first != 0)
            {
                overallPercentageChange = ((last - first) / first) * 100;
            }
        }

        trends.Summary = new TrendSummaryDto
        {
            TotalTenders = snapshots.Count,
            TotalItems = allRates.Select(r => new { r.ItemDescription, r.Uom }).Distinct().Count(),
            OverallAverageRate = allRates.Any() ? allRates.Average(r => r.NormalizedUnitRate) : 0,
            OverallPercentageChange = overallPercentageChange,
            OverallTrendDirection = GetTrendDirection(overallPercentageChange),
            AverageVolatility = CalculateVolatility(allRates.Select(r => r.NormalizedUnitRate).ToList()),
            TotalBidValue = totalBidValue
        };

        // Build trend points
        decimal? previousAverage = null;
        foreach (var snapshot in snapshots)
        {
            var rates = snapshot.ItemRates.ToList();
            var averageRate = rates.Any() ? rates.Average(r => r.NormalizedUnitRate) : 0;

            decimal percentageChangeFromPrevious = 0;
            if (previousAverage.HasValue && previousAverage.Value != 0)
            {
                percentageChangeFromPrevious = ((averageRate - previousAverage.Value) / previousAverage.Value) * 100;
            }

            trends.TrendPoints.Add(new VendorTrendPointDto
            {
                Date = snapshot.SnapshotDate,
                TenderReference = snapshot.Tender?.Reference ?? "Unknown",
                AverageRate = averageRate,
                MinRate = rates.Any() ? rates.Min(r => r.NormalizedUnitRate) : 0,
                MaxRate = rates.Any() ? rates.Max(r => r.NormalizedUnitRate) : 0,
                TotalBidAmount = snapshot.TotalBidAmount,
                ItemCount = snapshot.TotalItemsCount,
                Currency = snapshot.TenderBaseCurrency,
                PercentageChangeFromPrevious = percentageChangeFromPrevious
            });

            previousAverage = averageRate;
        }

        // Build item trends
        if (request.IncludeItemHistory)
        {
            var itemGroups = allRates
                .GroupBy(r => new { r.ItemDescription, r.Uom })
                .Take(request.MaxItemTrends)
                .ToList();

            foreach (var group in itemGroups)
            {
                var orderedRates = group
                    .OrderBy(r => r.Snapshot.SnapshotDate)
                    .ToList();

                var rateValues = orderedRates.Select(r => r.NormalizedUnitRate).ToList();

                if (!rateValues.Any())
                    continue;

                var firstRate = rateValues.First();
                var lastRate = rateValues.Last();
                var percentageChange = firstRate != 0 ? ((lastRate - firstRate) / firstRate) * 100 : 0;

                var itemTrend = new ItemTrendDto
                {
                    ItemDescription = group.Key.ItemDescription,
                    Uom = group.Key.Uom,
                    DataPointCount = rateValues.Count,
                    AverageRate = rateValues.Average(),
                    MinRate = rateValues.Min(),
                    MaxRate = rateValues.Max(),
                    LatestRate = lastRate,
                    PercentageChange = percentageChange,
                    TrendDirection = GetTrendDirection(percentageChange),
                    RateHistory = orderedRates.Select(r => new ItemRatePointDto
                    {
                        Date = r.Snapshot.SnapshotDate,
                        Rate = r.NormalizedUnitRate,
                        TenderReference = r.Snapshot.Tender?.Reference ?? "Unknown"
                    }).ToList()
                };

                trends.ItemTrends.Add(itemTrend);
            }

            // Sort by data point count descending (most tracked items first)
            trends.ItemTrends = trends.ItemTrends
                .OrderByDescending(i => i.DataPointCount)
                .ToList();
        }

        // Build tender participation
        if (request.IncludeTenderParticipation)
        {
            trends.TenderParticipation = snapshots.Select(s => new TenderParticipationDto
            {
                TenderId = s.TenderId,
                TenderReference = s.Tender?.Reference ?? "Unknown",
                TenderTitle = s.Tender?.Title ?? "Unknown",
                SubmissionDate = s.SnapshotDate,
                TotalBidAmount = s.TotalBidAmount,
                ItemCount = s.TotalItemsCount,
                Currency = s.TenderBaseCurrency,
                AverageItemRate = s.TotalItemsCount > 0 ? s.TotalBidAmount / s.TotalItemsCount : 0
            }).ToList();
        }

        return trends;
    }

    private static string GetTrendDirection(decimal percentageChange)
    {
        return percentageChange switch
        {
            > 5 => "up",
            < -5 => "down",
            _ => "stable"
        };
    }

    private static decimal CalculateVolatility(List<decimal> values)
    {
        if (values.Count < 2)
            return 0;

        var mean = values.Average();
        if (mean == 0)
            return 0;

        var sumOfSquares = values.Sum(v => (v - mean) * (v - mean));
        var stdDev = (decimal)Math.Sqrt((double)(sumOfSquares / values.Count));

        return (stdDev / mean) * 100;
    }
}
