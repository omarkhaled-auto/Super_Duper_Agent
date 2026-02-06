using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorAnalytics;

/// <summary>
/// Query to get analytics for a specific vendor's pricing data.
/// </summary>
public class GetVendorAnalyticsQuery : IRequest<VendorAnalyticsDto?>
{
    /// <summary>
    /// Bidder ID to get analytics for.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Optional start date for analytics period.
    /// </summary>
    public DateTime? FromDate { get; set; }

    /// <summary>
    /// Optional end date for analytics period.
    /// </summary>
    public DateTime? ToDate { get; set; }

    /// <summary>
    /// Maximum number of item analytics to return.
    /// </summary>
    public int MaxItemAnalytics { get; set; } = 50;

    /// <summary>
    /// Include tender summaries in response.
    /// </summary>
    public bool IncludeTenderSummaries { get; set; } = true;
}
