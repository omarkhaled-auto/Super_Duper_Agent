namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for vendor rate trends over time.
/// </summary>
public class VendorTrendsDto
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
    /// Date range start.
    /// </summary>
    public DateTime? FromDate { get; set; }

    /// <summary>
    /// Date range end.
    /// </summary>
    public DateTime? ToDate { get; set; }

    /// <summary>
    /// Overall summary statistics.
    /// </summary>
    public TrendSummaryDto Summary { get; set; } = new();

    /// <summary>
    /// Rate trend data points for charting.
    /// </summary>
    public List<VendorTrendPointDto> TrendPoints { get; set; } = new();

    /// <summary>
    /// Per-item trend data.
    /// </summary>
    public List<ItemTrendDto> ItemTrends { get; set; } = new();

    /// <summary>
    /// Tender participation history.
    /// </summary>
    public List<TenderParticipationDto> TenderParticipation { get; set; } = new();
}

/// <summary>
/// Summary statistics for vendor trends.
/// </summary>
public class TrendSummaryDto
{
    /// <summary>
    /// Total number of tenders participated in.
    /// </summary>
    public int TotalTenders { get; set; }

    /// <summary>
    /// Total number of items priced.
    /// </summary>
    public int TotalItems { get; set; }

    /// <summary>
    /// Overall average rate.
    /// </summary>
    public decimal OverallAverageRate { get; set; }

    /// <summary>
    /// Overall percentage change (first to last).
    /// </summary>
    public decimal OverallPercentageChange { get; set; }

    /// <summary>
    /// Overall trend direction: "up", "down", or "stable".
    /// </summary>
    public string OverallTrendDirection { get; set; } = "stable";

    /// <summary>
    /// Average rate volatility.
    /// </summary>
    public decimal AverageVolatility { get; set; }

    /// <summary>
    /// Total bid value over the period.
    /// </summary>
    public decimal TotalBidValue { get; set; }
}

/// <summary>
/// Single data point in the trend chart.
/// </summary>
public class VendorTrendPointDto
{
    /// <summary>
    /// Date of the data point.
    /// </summary>
    public DateTime Date { get; set; }

    /// <summary>
    /// Tender reference for this data point.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Average rate at this point.
    /// </summary>
    public decimal AverageRate { get; set; }

    /// <summary>
    /// Minimum rate at this point.
    /// </summary>
    public decimal MinRate { get; set; }

    /// <summary>
    /// Maximum rate at this point.
    /// </summary>
    public decimal MaxRate { get; set; }

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

    /// <summary>
    /// Percentage change from previous point.
    /// </summary>
    public decimal PercentageChangeFromPrevious { get; set; }
}

/// <summary>
/// Trend data for a specific item.
/// </summary>
public class ItemTrendDto
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
    /// Number of data points.
    /// </summary>
    public int DataPointCount { get; set; }

    /// <summary>
    /// Average rate.
    /// </summary>
    public decimal AverageRate { get; set; }

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
    /// Percentage change from first to last.
    /// </summary>
    public decimal PercentageChange { get; set; }

    /// <summary>
    /// Trend direction: "up", "down", or "stable".
    /// </summary>
    public string TrendDirection { get; set; } = "stable";

    /// <summary>
    /// Historical rate data points.
    /// </summary>
    public List<ItemRatePointDto> RateHistory { get; set; } = new();
}

/// <summary>
/// Single rate data point for an item.
/// </summary>
public class ItemRatePointDto
{
    /// <summary>
    /// Date of the rate.
    /// </summary>
    public DateTime Date { get; set; }

    /// <summary>
    /// Rate value.
    /// </summary>
    public decimal Rate { get; set; }

    /// <summary>
    /// Tender reference.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;
}

/// <summary>
/// Tender participation record.
/// </summary>
public class TenderParticipationDto
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
    /// Submission date.
    /// </summary>
    public DateTime SubmissionDate { get; set; }

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

    /// <summary>
    /// Average item rate.
    /// </summary>
    public decimal AverageItemRate { get; set; }
}
