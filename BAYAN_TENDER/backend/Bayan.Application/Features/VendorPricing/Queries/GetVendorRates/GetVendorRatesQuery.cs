using Bayan.Application.Common.Models;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorRates;

/// <summary>
/// Query to get current/latest rates for a vendor by item.
/// </summary>
public class GetVendorRatesQuery : IRequest<PaginatedList<VendorItemRateDto>>
{
    /// <summary>
    /// Bidder ID to get rates for.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Page number (1-based).
    /// </summary>
    public int Page { get; set; } = 1;

    /// <summary>
    /// Number of items per page.
    /// </summary>
    public int PageSize { get; set; } = 20;

    /// <summary>
    /// Optional filter by item description (partial match).
    /// </summary>
    public string? ItemDescription { get; set; }

    /// <summary>
    /// Optional filter by unit of measurement.
    /// </summary>
    public string? Uom { get; set; }

    /// <summary>
    /// Optional filter by tender ID.
    /// </summary>
    public Guid? TenderId { get; set; }

    /// <summary>
    /// If true, only return the latest rate for each item.
    /// </summary>
    public bool LatestOnly { get; set; } = true;
}
