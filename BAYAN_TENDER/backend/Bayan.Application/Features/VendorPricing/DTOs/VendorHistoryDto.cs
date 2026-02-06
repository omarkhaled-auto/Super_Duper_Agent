namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for vendor pricing history with trend data.
/// </summary>
public class VendorHistoryDto
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
    /// Item description for the history.
    /// </summary>
    public string ItemDescription { get; set; } = string.Empty;

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Historical rate data points.
    /// </summary>
    public List<VendorRateHistoryPointDto> RateHistory { get; set; } = new();

    /// <summary>
    /// Average rate across all snapshots.
    /// </summary>
    public decimal AverageRate { get; set; }

    /// <summary>
    /// Minimum rate recorded.
    /// </summary>
    public decimal MinRate { get; set; }

    /// <summary>
    /// Maximum rate recorded.
    /// </summary>
    public decimal MaxRate { get; set; }

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
/// Data point representing a rate at a specific point in time.
/// </summary>
public class VendorRateHistoryPointDto
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
    /// Tender reference this rate came from.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Currency of the rate.
    /// </summary>
    public string Currency { get; set; } = string.Empty;
}
