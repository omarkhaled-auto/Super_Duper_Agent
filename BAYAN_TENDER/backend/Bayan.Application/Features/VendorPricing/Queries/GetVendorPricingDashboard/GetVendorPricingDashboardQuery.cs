using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorPricingDashboard;

/// <summary>
/// Query to get vendor pricing dashboard data.
/// </summary>
public class GetVendorPricingDashboardQuery : IRequest<VendorPricingDashboardDto>
{
    /// <summary>
    /// Optional start date for filtering data.
    /// </summary>
    public DateTime? FromDate { get; set; }

    /// <summary>
    /// Optional end date for filtering data.
    /// </summary>
    public DateTime? ToDate { get; set; }

    /// <summary>
    /// Optional trade specialization filter.
    /// </summary>
    public string? TradeSpecialization { get; set; }

    /// <summary>
    /// Maximum number of top vendors to return.
    /// </summary>
    public int TopVendorsLimit { get; set; } = 10;

    /// <summary>
    /// Maximum number of recent snapshots to return.
    /// </summary>
    public int RecentSnapshotsLimit { get; set; } = 10;
}
