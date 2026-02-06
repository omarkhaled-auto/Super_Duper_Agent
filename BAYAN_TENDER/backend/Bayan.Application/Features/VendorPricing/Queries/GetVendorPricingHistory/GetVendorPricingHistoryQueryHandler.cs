using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorPricingHistory;

/// <summary>
/// Handler for GetVendorPricingHistoryQuery.
/// </summary>
public class GetVendorPricingHistoryQueryHandler
    : IRequestHandler<GetVendorPricingHistoryQuery, List<VendorHistoryDto>>
{
    private readonly IApplicationDbContext _context;

    public GetVendorPricingHistoryQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<VendorHistoryDto>> Handle(
        GetVendorPricingHistoryQuery request,
        CancellationToken cancellationToken)
    {
        // Get bidder info
        var bidder = await _context.Bidders
            .AsNoTracking()
            .FirstOrDefaultAsync(b => b.Id == request.BidderId, cancellationToken);

        if (bidder == null)
        {
            return new List<VendorHistoryDto>();
        }

        // Build query for item rates
        var ratesQuery = _context.VendorItemRates
            .AsNoTracking()
            .Include(r => r.Snapshot)
                .ThenInclude(s => s.Tender)
            .Where(r => r.Snapshot.BidderId == request.BidderId);

        // Apply filters
        if (!string.IsNullOrWhiteSpace(request.ItemDescription))
        {
            var descTerm = request.ItemDescription.ToLower();
            ratesQuery = ratesQuery.Where(r => r.ItemDescription.ToLower().Contains(descTerm));
        }

        if (!string.IsNullOrWhiteSpace(request.Uom))
        {
            ratesQuery = ratesQuery.Where(r => r.Uom.ToLower() == request.Uom.ToLower());
        }

        if (request.FromDate.HasValue)
        {
            ratesQuery = ratesQuery.Where(r => r.Snapshot.SnapshotDate >= request.FromDate.Value);
        }

        if (request.ToDate.HasValue)
        {
            ratesQuery = ratesQuery.Where(r => r.Snapshot.SnapshotDate <= request.ToDate.Value);
        }

        // Get all rates
        var rates = await ratesQuery.ToListAsync(cancellationToken);

        // Group by item description and UOM to create history entries
        var groupedRates = rates
            .GroupBy(r => new { r.ItemDescription, r.Uom })
            .Take(request.MaxItems)
            .ToList();

        var result = new List<VendorHistoryDto>();

        foreach (var group in groupedRates)
        {
            var orderedRates = group.OrderBy(r => r.Snapshot.SnapshotDate).ToList();

            if (!orderedRates.Any())
                continue;

            var rateValues = orderedRates.Select(r => r.NormalizedUnitRate).ToList();
            var firstRate = rateValues.First();
            var lastRate = rateValues.Last();

            var history = new VendorHistoryDto
            {
                BidderId = request.BidderId,
                BidderName = bidder.CompanyName,
                ItemDescription = group.Key.ItemDescription,
                Uom = group.Key.Uom,
                AverageRate = rateValues.Average(),
                MinRate = rateValues.Min(),
                MaxRate = rateValues.Max(),
                RateHistory = orderedRates.Select(r => new VendorRateHistoryPointDto
                {
                    Date = r.Snapshot.SnapshotDate,
                    Rate = r.NormalizedUnitRate,
                    TenderReference = r.Snapshot.Tender?.Reference ?? "Unknown",
                    Currency = r.NormalizedCurrency
                }).ToList()
            };

            // Calculate trend
            if (firstRate != 0)
            {
                history.PercentageChange = ((lastRate - firstRate) / firstRate) * 100;
            }

            history.TrendDirection = history.PercentageChange switch
            {
                > 5 => "up",
                < -5 => "down",
                _ => "stable"
            };

            result.Add(history);
        }

        return result;
    }
}
