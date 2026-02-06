using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorPricingDashboard;

/// <summary>
/// Handler for GetVendorPricingDashboardQuery.
/// </summary>
public class GetVendorPricingDashboardQueryHandler
    : IRequestHandler<GetVendorPricingDashboardQuery, VendorPricingDashboardDto>
{
    private readonly IApplicationDbContext _context;

    public GetVendorPricingDashboardQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<VendorPricingDashboardDto> Handle(
        GetVendorPricingDashboardQuery request,
        CancellationToken cancellationToken)
    {
        var dashboard = new VendorPricingDashboardDto();
        var now = DateTime.UtcNow;
        var startOfMonth = new DateTime(now.Year, now.Month, 1, 0, 0, 0, DateTimeKind.Utc);

        // Build base query for snapshots
        var snapshotsQuery = _context.VendorPricingSnapshots
            .AsNoTracking()
            .Include(s => s.Bidder)
            .Include(s => s.Tender)
            .AsQueryable();

        if (request.FromDate.HasValue)
        {
            snapshotsQuery = snapshotsQuery.Where(s => s.SnapshotDate >= request.FromDate.Value);
        }

        if (request.ToDate.HasValue)
        {
            snapshotsQuery = snapshotsQuery.Where(s => s.SnapshotDate <= request.ToDate.Value);
        }

        if (!string.IsNullOrWhiteSpace(request.TradeSpecialization))
        {
            snapshotsQuery = snapshotsQuery.Where(s =>
                s.Bidder.TradeSpecialization != null &&
                s.Bidder.TradeSpecialization.Contains(request.TradeSpecialization));
        }

        var snapshots = await snapshotsQuery.ToListAsync(cancellationToken);

        // Calculate summary statistics
        var uniqueBidderIds = snapshots.Select(s => s.BidderId).Distinct().ToList();
        var totalBidValue = snapshots.Sum(s => s.TotalBidAmount);
        var snapshotsThisMonth = snapshots.Count(s => s.SnapshotDate >= startOfMonth);

        // Get unique items count
        var uniqueItemsCount = await _context.VendorItemRates
            .AsNoTracking()
            .Where(r => snapshots.Select(s => s.Id).Contains(r.SnapshotId))
            .Select(r => new { r.ItemDescription, r.Uom })
            .Distinct()
            .CountAsync(cancellationToken);

        // Get new vendors this month
        var newVendorsThisMonth = await _context.VendorPricingSnapshots
            .AsNoTracking()
            .GroupBy(s => s.BidderId)
            .Select(g => new { BidderId = g.Key, FirstSnapshot = g.Min(s => s.SnapshotDate) })
            .CountAsync(g => g.FirstSnapshot >= startOfMonth, cancellationToken);

        dashboard.Summary = new VendorDashboardSummaryDto
        {
            TotalVendors = uniqueBidderIds.Count,
            TotalSnapshots = snapshots.Count,
            TotalUniqueItems = uniqueItemsCount,
            TotalBidValue = totalBidValue,
            AverageBidAmount = snapshots.Count > 0 ? totalBidValue / snapshots.Count : 0,
            SnapshotsThisMonth = snapshotsThisMonth,
            NewVendorsThisMonth = newVendorsThisMonth,
            DefaultCurrency = "AED"
        };

        // Get top vendors
        var topVendors = snapshots
            .GroupBy(s => new { s.BidderId, s.Bidder.CompanyName, s.Bidder.TradeSpecialization })
            .Select(g => new TopVendorDto
            {
                BidderId = g.Key.BidderId,
                BidderName = g.Key.CompanyName,
                TradeSpecialization = g.Key.TradeSpecialization,
                SnapshotCount = g.Count(),
                TotalBidValue = g.Sum(s => s.TotalBidAmount),
                AverageRateTrend = CalculateTrend(g.OrderBy(s => s.SnapshotDate).ToList()),
                TrendDirection = GetTrendDirection(CalculateTrend(g.OrderBy(s => s.SnapshotDate).ToList()))
            })
            .OrderByDescending(v => v.TotalBidValue)
            .Take(request.TopVendorsLimit)
            .ToList();

        dashboard.TopVendors = topVendors;

        // Get recent snapshots
        dashboard.RecentSnapshots = snapshots
            .OrderByDescending(s => s.SnapshotDate)
            .Take(request.RecentSnapshotsLimit)
            .Select(s => new RecentSnapshotDto
            {
                Id = s.Id,
                BidderId = s.BidderId,
                BidderName = s.Bidder.CompanyName,
                TenderId = s.TenderId,
                TenderReference = s.Tender?.Reference ?? "Unknown",
                TenderTitle = s.Tender?.Title ?? "Unknown",
                SnapshotDate = s.SnapshotDate,
                TotalBidAmount = s.TotalBidAmount,
                ItemCount = s.TotalItemsCount,
                Currency = s.TenderBaseCurrency
            })
            .ToList();

        // Calculate rate trends (monthly aggregation)
        var rateTrends = snapshots
            .GroupBy(s => new DateTime(s.SnapshotDate.Year, s.SnapshotDate.Month, 1))
            .OrderBy(g => g.Key)
            .Select(g => new RateTrendDataPointDto
            {
                Date = g.Key,
                AverageRate = g.Average(s => s.TotalBidAmount / (s.TotalItemsCount > 0 ? s.TotalItemsCount : 1)),
                DataPointCount = g.Count()
            })
            .ToList();

        dashboard.RateTrends = rateTrends;

        // Trade breakdown
        var tradeBreakdown = snapshots
            .GroupBy(s => s.Bidder.TradeSpecialization ?? "Unspecified")
            .Select(g => new TradeBreakdownDto
            {
                Trade = g.Key,
                VendorCount = g.Select(s => s.BidderId).Distinct().Count(),
                TotalValue = g.Sum(s => s.TotalBidAmount),
                Percentage = totalBidValue > 0 ? (g.Sum(s => s.TotalBidAmount) / totalBidValue) * 100 : 0
            })
            .OrderByDescending(t => t.TotalValue)
            .ToList();

        dashboard.TradeBreakdown = tradeBreakdown;

        return dashboard;
    }

    private static decimal CalculateTrend(List<Domain.Entities.VendorPricingSnapshot> snapshots)
    {
        if (snapshots.Count < 2)
            return 0;

        var first = snapshots.First();
        var last = snapshots.Last();

        if (first.TotalBidAmount == 0)
            return 0;

        return ((last.TotalBidAmount - first.TotalBidAmount) / first.TotalBidAmount) * 100;
    }

    private static string GetTrendDirection(decimal trend)
    {
        return trend switch
        {
            > 5 => "up",
            < -5 => "down",
            _ => "stable"
        };
    }
}
