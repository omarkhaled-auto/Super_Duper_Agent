using Bayan.Domain.Enums;

namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Data transfer object for bid pricing information.
/// </summary>
public class BidPricingDto
{
    /// <summary>
    /// Unique identifier for the bid pricing item.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Bid submission this pricing belongs to.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Matched BOQ item (null if extra item).
    /// </summary>
    public Guid? BoqItemId { get; set; }

    /// <summary>
    /// Bidder's item number.
    /// </summary>
    public string? BidderItemNumber { get; set; }

    /// <summary>
    /// Bidder's description.
    /// </summary>
    public string? BidderDescription { get; set; }

    /// <summary>
    /// Bidder's quantity.
    /// </summary>
    public decimal? BidderQuantity { get; set; }

    /// <summary>
    /// Bidder's unit of measurement.
    /// </summary>
    public string? BidderUom { get; set; }

    // Native values
    /// <summary>
    /// Unit rate in native currency.
    /// </summary>
    public decimal? NativeUnitRate { get; set; }

    /// <summary>
    /// Total amount in native currency.
    /// </summary>
    public decimal? NativeAmount { get; set; }

    /// <summary>
    /// Native currency code.
    /// </summary>
    public string NativeCurrency { get; set; } = string.Empty;

    // Normalized values
    /// <summary>
    /// Normalized unit rate (base currency and UOM).
    /// </summary>
    public decimal? NormalizedUnitRate { get; set; }

    /// <summary>
    /// Normalized total amount.
    /// </summary>
    public decimal? NormalizedAmount { get; set; }

    /// <summary>
    /// Exchange rate applied.
    /// </summary>
    public decimal? FxRateApplied { get; set; }

    /// <summary>
    /// UOM conversion factor applied.
    /// </summary>
    public decimal? UomConversionFactor { get; set; }

    // Match info
    /// <summary>
    /// Type of match with master BOQ.
    /// </summary>
    public Domain.Enums.MatchType? MatchType { get; set; }

    /// <summary>
    /// Match confidence percentage (0-100).
    /// </summary>
    public decimal? MatchConfidence { get; set; }

    /// <summary>
    /// Whether included in total calculation.
    /// </summary>
    public bool IsIncludedInTotal { get; set; }

    // Outlier info
    /// <summary>
    /// Whether this is an outlier.
    /// </summary>
    public bool IsOutlier { get; set; }

    /// <summary>
    /// Outlier severity level.
    /// </summary>
    public OutlierSeverity? OutlierSeverity { get; set; }

    /// <summary>
    /// Percentage deviation from average.
    /// </summary>
    public decimal? DeviationFromAverage { get; set; }

    /// <summary>
    /// Whether there's a formula error.
    /// </summary>
    public bool HasFormulaError { get; set; }

    /// <summary>
    /// Whether bidder did not bid on this item.
    /// </summary>
    public bool IsNoBid { get; set; }

    /// <summary>
    /// Whether the item is non-comparable (UOM cannot be converted).
    /// </summary>
    public bool IsNonComparable { get; set; }

    /// <summary>
    /// Additional notes.
    /// </summary>
    public string? Notes { get; set; }

    // BOQ item reference info
    /// <summary>
    /// Matched BOQ item number.
    /// </summary>
    public string? BoqItemNumber { get; set; }

    /// <summary>
    /// Matched BOQ item description.
    /// </summary>
    public string? BoqDescription { get; set; }

    /// <summary>
    /// Matched BOQ quantity.
    /// </summary>
    public decimal? BoqQuantity { get; set; }

    /// <summary>
    /// Matched BOQ unit of measurement.
    /// </summary>
    public string? BoqUom { get; set; }
}
