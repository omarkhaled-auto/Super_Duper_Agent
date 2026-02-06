namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for vendor pricing analytics.
/// </summary>
public class VendorAnalyticsDto
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
    /// Total number of pricing snapshots.
    /// </summary>
    public int TotalSnapshots { get; set; }

    /// <summary>
    /// Total number of unique items priced.
    /// </summary>
    public int TotalUniqueItems { get; set; }

    /// <summary>
    /// Date of the first snapshot.
    /// </summary>
    public DateTime? FirstSnapshotDate { get; set; }

    /// <summary>
    /// Date of the most recent snapshot.
    /// </summary>
    public DateTime? LastSnapshotDate { get; set; }

    /// <summary>
    /// Average bid amount across all tenders.
    /// </summary>
    public decimal AverageBidAmount { get; set; }

    /// <summary>
    /// Overall trend direction: "up", "down", or "stable".
    /// </summary>
    public string OverallTrendDirection { get; set; } = string.Empty;

    /// <summary>
    /// Average rate volatility (standard deviation / mean).
    /// </summary>
    public decimal AverageVolatility { get; set; }

    /// <summary>
    /// Per-item analytics.
    /// </summary>
    public List<VendorItemAnalyticsDto> ItemAnalytics { get; set; } = new();

    /// <summary>
    /// Summary of tenders participated in.
    /// </summary>
    public List<VendorTenderSummaryDto> TenderSummaries { get; set; } = new();
}

/// <summary>
/// Analytics for a specific item from a vendor.
/// </summary>
public class VendorItemAnalyticsDto
{
    /// <summary>
    /// Item description.
    /// </summary>
    public string ItemDescription { get; set; } = string.Empty;

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Number of data points for this item.
    /// </summary>
    public int DataPointCount { get; set; }

    /// <summary>
    /// Average rate.
    /// </summary>
    public decimal AverageRate { get; set; }

    /// <summary>
    /// Standard deviation of rates.
    /// </summary>
    public decimal StandardDeviation { get; set; }

    /// <summary>
    /// Volatility (coefficient of variation): StdDev / Mean.
    /// </summary>
    public decimal Volatility { get; set; }

    /// <summary>
    /// Minimum rate.
    /// </summary>
    public decimal MinRate { get; set; }

    /// <summary>
    /// Maximum rate.
    /// </summary>
    public decimal MaxRate { get; set; }

    /// <summary>
    /// Most recent rate.
    /// </summary>
    public decimal LatestRate { get; set; }

    /// <summary>
    /// Trend direction: "up", "down", or "stable".
    /// </summary>
    public string TrendDirection { get; set; } = string.Empty;

    /// <summary>
    /// Percentage change from first to last rate.
    /// </summary>
    public decimal PercentageChange { get; set; }
}

/// <summary>
/// Summary of vendor participation in a tender.
/// </summary>
public class VendorTenderSummaryDto
{
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
    /// Date of the bid submission.
    /// </summary>
    public DateTime SnapshotDate { get; set; }

    /// <summary>
    /// Total bid amount.
    /// </summary>
    public decimal TotalBidAmount { get; set; }

    /// <summary>
    /// Number of items priced.
    /// </summary>
    public int ItemCount { get; set; }

    /// <summary>
    /// Currency.
    /// </summary>
    public string Currency { get; set; } = string.Empty;
}
