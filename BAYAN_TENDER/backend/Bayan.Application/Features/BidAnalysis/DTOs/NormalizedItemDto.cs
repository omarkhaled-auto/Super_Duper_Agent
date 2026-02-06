namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Represents a normalized bid pricing item after FX and UOM conversion.
/// </summary>
public class NormalizedItemDto
{
    /// <summary>
    /// Bid pricing line item identifier.
    /// </summary>
    public Guid BidPricingId { get; set; }

    /// <summary>
    /// Matched BOQ item identifier (null if unmatched).
    /// </summary>
    public Guid? BoqItemId { get; set; }

    /// <summary>
    /// Item number from the BOQ or bidder's submission.
    /// </summary>
    public string ItemNumber { get; set; } = string.Empty;

    /// <summary>
    /// Item description.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Original quantity from bidder.
    /// </summary>
    public decimal? OriginalQuantity { get; set; }

    /// <summary>
    /// Original UOM from bidder.
    /// </summary>
    public string? OriginalUom { get; set; }

    /// <summary>
    /// Original unit rate in native currency.
    /// </summary>
    public decimal? OriginalUnitRate { get; set; }

    /// <summary>
    /// Original total amount in native currency.
    /// </summary>
    public decimal? OriginalAmount { get; set; }

    /// <summary>
    /// Native currency code.
    /// </summary>
    public string NativeCurrency { get; set; } = string.Empty;

    /// <summary>
    /// Exchange rate applied for normalization.
    /// </summary>
    public decimal FxRateApplied { get; set; } = 1.0m;

    /// <summary>
    /// UOM conversion factor applied.
    /// </summary>
    public decimal? UomConversionFactor { get; set; }

    /// <summary>
    /// Normalized unit rate in base currency.
    /// </summary>
    public decimal? NormalizedUnitRate { get; set; }

    /// <summary>
    /// Normalized total amount in base currency.
    /// </summary>
    public decimal? NormalizedAmount { get; set; }

    /// <summary>
    /// Target UOM after normalization.
    /// </summary>
    public string? NormalizedUom { get; set; }

    /// <summary>
    /// Base currency code.
    /// </summary>
    public string BaseCurrency { get; set; } = "AED";

    /// <summary>
    /// Whether the item is non-comparable due to UOM incompatibility.
    /// </summary>
    public bool IsNonComparable { get; set; }

    /// <summary>
    /// Reason for non-comparability.
    /// </summary>
    public string? NonComparableReason { get; set; }
}
