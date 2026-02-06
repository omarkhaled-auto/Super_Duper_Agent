using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a pricing line item from a bid submission.
/// </summary>
public class BidPricing : BaseEntity
{
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

    /// <summary>
    /// Type of match with master BOQ.
    /// </summary>
    public Enums.MatchType? MatchType { get; set; }

    /// <summary>
    /// Match confidence percentage.
    /// </summary>
    public decimal? MatchConfidence { get; set; }

    /// <summary>
    /// Whether included in total calculation.
    /// </summary>
    public bool IsIncludedInTotal { get; set; } = true;

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

    // Navigation properties
    /// <summary>
    /// Bid submission associated with this pricing.
    /// </summary>
    public virtual BidSubmission BidSubmission { get; set; } = null!;

    /// <summary>
    /// Matched BOQ item.
    /// </summary>
    public virtual BoqItem? BoqItem { get; set; }
}
