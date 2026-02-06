namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for vendor pricing dashboard data.
/// </summary>
public class VendorPricingDashboardDto
{
    /// <summary>
    /// Summary statistics for the dashboard.
    /// </summary>
    public VendorDashboardSummaryDto Summary { get; set; } = new();

    /// <summary>
    /// Top vendors by volume.
    /// </summary>
    public List<TopVendorDto> TopVendors { get; set; } = new();

    /// <summary>
    /// Recent pricing snapshots.
    /// </summary>
    public List<RecentSnapshotDto> RecentSnapshots { get; set; } = new();

    /// <summary>
    /// Rate trend data for charting.
    /// </summary>
    public List<RateTrendDataPointDto> RateTrends { get; set; } = new();

    /// <summary>
    /// Trade breakdown for pie chart.
    /// </summary>
    public List<TradeBreakdownDto> TradeBreakdown { get; set; } = new();
}

/// <summary>
/// Summary statistics for vendor pricing dashboard.
/// </summary>
public class VendorDashboardSummaryDto
{
    /// <summary>
    /// Total number of vendors with pricing data.
    /// </summary>
    public int TotalVendors { get; set; }

    /// <summary>
    /// Total number of pricing snapshots.
    /// </summary>
    public int TotalSnapshots { get; set; }

    /// <summary>
    /// Total number of unique items tracked.
    /// </summary>
    public int TotalUniqueItems { get; set; }

    /// <summary>
    /// Total value of all bids tracked.
    /// </summary>
    public decimal TotalBidValue { get; set; }

    /// <summary>
    /// Average bid amount.
    /// </summary>
    public decimal AverageBidAmount { get; set; }

    /// <summary>
    /// Number of snapshots created this month.
    /// </summary>
    public int SnapshotsThisMonth { get; set; }

    /// <summary>
    /// Number of new vendors this month.
    /// </summary>
    public int NewVendorsThisMonth { get; set; }

    /// <summary>
    /// Default currency for display.
    /// </summary>
    public string DefaultCurrency { get; set; } = "AED";
}

/// <summary>
/// Top vendor by pricing volume.
/// </summary>
public class TopVendorDto
{
    /// <summary>
    /// Bidder identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderName { get; set; } = string.Empty;

    /// <summary>
    /// Trade specialization.
    /// </summary>
    public string? TradeSpecialization { get; set; }

    /// <summary>
    /// Total number of snapshots.
    /// </summary>
    public int SnapshotCount { get; set; }

    /// <summary>
    /// Total bid value.
    /// </summary>
    public decimal TotalBidValue { get; set; }

    /// <summary>
    /// Average rate trend (percentage change).
    /// </summary>
    public decimal AverageRateTrend { get; set; }

    /// <summary>
    /// Trend direction: "up", "down", or "stable".
    /// </summary>
    public string TrendDirection { get; set; } = "stable";
}

/// <summary>
/// Recent pricing snapshot for dashboard.
/// </summary>
public class RecentSnapshotDto
{
    /// <summary>
    /// Snapshot identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Bidder identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderName { get; set; } = string.Empty;

    /// <summary>
    /// Tender identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender reference.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Date of snapshot.
    /// </summary>
    public DateTime SnapshotDate { get; set; }

    /// <summary>
    /// Total bid amount.
    /// </summary>
    public decimal TotalBidAmount { get; set; }

    /// <summary>
    /// Number of items.
    /// </summary>
    public int ItemCount { get; set; }

    /// <summary>
    /// Currency.
    /// </summary>
    public string Currency { get; set; } = string.Empty;
}

/// <summary>
/// Data point for rate trend chart.
/// </summary>
public class RateTrendDataPointDto
{
    /// <summary>
    /// Date of the data point.
    /// </summary>
    public DateTime Date { get; set; }

    /// <summary>
    /// Average rate value.
    /// </summary>
    public decimal AverageRate { get; set; }

    /// <summary>
    /// Number of data points for this date.
    /// </summary>
    public int DataPointCount { get; set; }
}

/// <summary>
/// Trade breakdown for pie chart.
/// </summary>
public class TradeBreakdownDto
{
    /// <summary>
    /// Trade specialization.
    /// </summary>
    public string Trade { get; set; } = string.Empty;

    /// <summary>
    /// Number of vendors in this trade.
    /// </summary>
    public int VendorCount { get; set; }

    /// <summary>
    /// Total value for this trade.
    /// </summary>
    public decimal TotalValue { get; set; }

    /// <summary>
    /// Percentage of total.
    /// </summary>
    public decimal Percentage { get; set; }
}
