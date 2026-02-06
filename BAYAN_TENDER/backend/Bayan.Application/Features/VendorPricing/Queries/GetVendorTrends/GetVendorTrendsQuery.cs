using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorTrends;

/// <summary>
/// Query to get vendor rate trends over time.
/// </summary>
public class GetVendorTrendsQuery : IRequest<VendorTrendsDto?>
{
    /// <summary>
    /// Bidder ID to get trends for.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Optional start date for trends period.
    /// </summary>
    public DateTime? FromDate { get; set; }

    /// <summary>
    /// Optional end date for trends period.
    /// </summary>
    public DateTime? ToDate { get; set; }

    /// <summary>
    /// Maximum number of item trends to return.
    /// </summary>
    public int MaxItemTrends { get; set; } = 50;

    /// <summary>
    /// Include item-level rate history.
    /// </summary>
    public bool IncludeItemHistory { get; set; } = true;

    /// <summary>
    /// Include tender participation details.
    /// </summary>
    public bool IncludeTenderParticipation { get; set; } = true;
}
