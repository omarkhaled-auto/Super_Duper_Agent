using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorPricingHistory;

/// <summary>
/// Query to get vendor pricing history for a specific bidder.
/// </summary>
public class GetVendorPricingHistoryQuery : IRequest<List<VendorHistoryDto>>
{
    /// <summary>
    /// Bidder ID to get history for.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Optional filter by item description (partial match).
    /// </summary>
    public string? ItemDescription { get; set; }

    /// <summary>
    /// Optional filter by unit of measurement.
    /// </summary>
    public string? Uom { get; set; }

    /// <summary>
    /// Optional start date for history range.
    /// </summary>
    public DateTime? FromDate { get; set; }

    /// <summary>
    /// Optional end date for history range.
    /// </summary>
    public DateTime? ToDate { get; set; }

    /// <summary>
    /// Maximum number of items to return. Default is 50.
    /// </summary>
    public int MaxItems { get; set; } = 50;
}
