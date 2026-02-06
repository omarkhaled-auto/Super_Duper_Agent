using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.VendorPricing.Queries.CompareVendorRates;

/// <summary>
/// Handler for CompareVendorRatesQuery.
/// </summary>
public class CompareVendorRatesQueryHandler
    : IRequestHandler<CompareVendorRatesQuery, VendorComparisonDto>
{
    private readonly IApplicationDbContext _context;

    public CompareVendorRatesQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<VendorComparisonDto> Handle(
        CompareVendorRatesQuery request,
        CancellationToken cancellationToken)
    {
        var result = new VendorComparisonDto();

        // Get bidder information
        var bidders = await _context.Bidders
            .AsNoTracking()
            .Where(b => request.BidderIds.Contains(b.Id))
            .ToListAsync(cancellationToken);

        // Build base query for rates
        var ratesQuery = _context.VendorItemRates
            .AsNoTracking()
            .Include(r => r.Snapshot)
                .ThenInclude(s => s.Tender)
            .Where(r => request.BidderIds.Contains(r.Snapshot.BidderId));

        // Apply item description filter
        if (request.ItemDescriptions != null && request.ItemDescriptions.Any())
        {
            var lowerDescriptions = request.ItemDescriptions.Select(d => d.ToLower()).ToList();
            ratesQuery = ratesQuery.Where(r =>
                lowerDescriptions.Any(d => r.ItemDescription.ToLower().Contains(d)));
        }

        // Apply UOM filter
        if (!string.IsNullOrWhiteSpace(request.Uom))
        {
            ratesQuery = ratesQuery.Where(r => r.Uom.ToLower() == request.Uom.ToLower());
        }

        var allRates = await ratesQuery.ToListAsync(cancellationToken);

        // If latest rates only, keep only the latest for each bidder/item combination
        if (request.LatestRatesOnly)
        {
            allRates = allRates
                .GroupBy(r => new { r.Snapshot.BidderId, r.ItemDescription, r.Uom })
                .Select(g => g.OrderByDescending(r => r.Snapshot.SnapshotDate).First())
                .ToList();
        }

        // Group rates by item description and UOM
        var itemGroups = allRates
            .GroupBy(r => new { r.ItemDescription, r.Uom })
            .Take(request.MaxItems)
            .ToList();

        // Build comparison items
        var comparisonItems = new List<VendorComparisonItemDto>();
        var vendorTotals = new Dictionary<Guid, decimal>();

        foreach (var group in itemGroups)
        {
            var comparisonItem = new VendorComparisonItemDto
            {
                ItemDescription = group.Key.ItemDescription,
                Uom = group.Key.Uom,
                VendorRates = new Dictionary<Guid, VendorComparisonRateDto>()
            };

            var ratesForItem = group.ToList();
            var rateValues = ratesForItem.Select(r => r.NormalizedUnitRate).ToList();

            if (rateValues.Any())
            {
                comparisonItem.AverageRate = rateValues.Average();
                comparisonItem.MinRate = rateValues.Min();
                comparisonItem.MaxRate = rateValues.Max();
            }

            foreach (var rate in ratesForItem)
            {
                var bidderId = rate.Snapshot.BidderId;

                var vendorRate = new VendorComparisonRateDto
                {
                    Rate = rate.NormalizedUnitRate,
                    SnapshotDate = rate.Snapshot.SnapshotDate,
                    TenderReference = rate.Snapshot.Tender?.Reference ?? "Unknown"
                };

                if (comparisonItem.AverageRate != 0)
                {
                    vendorRate.DeviationFromAverage =
                        ((rate.NormalizedUnitRate - comparisonItem.AverageRate) / comparisonItem.AverageRate) * 100;
                }

                vendorRate.IsLowest = rate.NormalizedUnitRate == comparisonItem.MinRate;

                if (vendorRate.IsLowest)
                {
                    comparisonItem.LowestBidderId = bidderId;
                }

                comparisonItem.VendorRates[bidderId] = vendorRate;

                // Track vendor totals
                if (!vendorTotals.ContainsKey(bidderId))
                {
                    vendorTotals[bidderId] = 0;
                }
                vendorTotals[bidderId] += rate.NormalizedUnitRate;
            }

            comparisonItems.Add(comparisonItem);
        }

        result.Items = comparisonItems;

        // Build vendor summaries
        var sortedVendors = vendorTotals.OrderBy(v => v.Value).ToList();
        var rank = 1;

        foreach (var vendor in sortedVendors)
        {
            var bidder = bidders.FirstOrDefault(b => b.Id == vendor.Key);
            var vendorDto = new VendorComparisonVendorDto
            {
                BidderId = vendor.Key,
                CompanyName = bidder?.CompanyName ?? "Unknown",
                ItemsWithPricing = comparisonItems.Count(i => i.VendorRates.ContainsKey(vendor.Key)),
                TotalAmount = vendor.Value,
                Rank = rank++
            };

            result.Vendors.Add(vendorDto);
        }

        // Build summary
        result.Summary = new VendorComparisonSummaryDto
        {
            TotalItemsCompared = comparisonItems.Count,
            ItemsWithAllVendorPricing = comparisonItems.Count(i =>
                i.VendorRates.Count == request.BidderIds.Count)
        };

        if (sortedVendors.Any())
        {
            var lowestVendor = sortedVendors.First();
            result.Summary.OverallLowestBidderId = lowestVendor.Key;
            result.Summary.OverallLowestBidderName =
                bidders.FirstOrDefault(b => b.Id == lowestVendor.Key)?.CompanyName;

            if (sortedVendors.Count > 1)
            {
                var highestVendor = sortedVendors.Last();
                result.Summary.PotentialSavings = highestVendor.Value - lowestVendor.Value;
            }
        }

        return result;
    }
}
