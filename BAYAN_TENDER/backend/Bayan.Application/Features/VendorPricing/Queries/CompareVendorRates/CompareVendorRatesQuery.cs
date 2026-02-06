using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Queries.CompareVendorRates;

/// <summary>
/// Query to compare rates between multiple vendors.
/// </summary>
public class CompareVendorRatesQuery : IRequest<VendorComparisonDto>
{
    /// <summary>
    /// List of bidder IDs to compare (2-5 vendors).
    /// </summary>
    public List<Guid> BidderIds { get; set; } = new();

    /// <summary>
    /// Optional list of item descriptions to compare.
    /// If empty, compares all common items.
    /// </summary>
    public List<string>? ItemDescriptions { get; set; }

    /// <summary>
    /// Optional filter by unit of measurement.
    /// </summary>
    public string? Uom { get; set; }

    /// <summary>
    /// Use latest rates only (vs. all historical rates).
    /// </summary>
    public bool LatestRatesOnly { get; set; } = true;

    /// <summary>
    /// Maximum number of items to compare.
    /// </summary>
    public int MaxItems { get; set; } = 100;
}
