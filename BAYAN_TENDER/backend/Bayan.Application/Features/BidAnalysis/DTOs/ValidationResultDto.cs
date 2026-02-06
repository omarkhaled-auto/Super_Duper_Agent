namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Result of bid import validation including formula checks, data validation, and coverage analysis.
/// </summary>
public class ValidationResultDto
{
    /// <summary>
    /// Bid submission identifier.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Tender identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Total number of items validated.
    /// </summary>
    public int TotalItemCount { get; set; }

    /// <summary>
    /// Number of items that passed validation.
    /// </summary>
    public int ValidCount { get; set; }

    /// <summary>
    /// Number of items with errors (blocking).
    /// </summary>
    public int ErrorCount { get; set; }

    /// <summary>
    /// Number of items with warnings (non-blocking).
    /// </summary>
    public int WarningCount { get; set; }

    /// <summary>
    /// Number of informational notes.
    /// </summary>
    public int InfoCount { get; set; }

    /// <summary>
    /// Whether the bid passes validation (no blocking errors).
    /// </summary>
    public bool IsValid => ErrorCount == 0;

    /// <summary>
    /// Formula check results.
    /// </summary>
    public FormulaCheckResultDto FormulaCheck { get; set; } = new();

    /// <summary>
    /// Data validation results.
    /// </summary>
    public DataValidationResultDto DataValidation { get; set; } = new();

    /// <summary>
    /// Coverage check results.
    /// </summary>
    public CoverageCheckResultDto CoverageCheck { get; set; } = new();

    /// <summary>
    /// Outlier detection results (if other bids are already imported).
    /// </summary>
    public OutlierDetectionResultDto? OutlierDetection { get; set; }

    /// <summary>
    /// All validation issues found.
    /// </summary>
    public List<ValidationIssueDto> Issues { get; set; } = new();

    /// <summary>
    /// Timestamp of validation.
    /// </summary>
    public DateTime ValidatedAt { get; set; }
}

/// <summary>
/// Formula check results (Amount = Qty x Rate).
/// </summary>
public class FormulaCheckResultDto
{
    /// <summary>
    /// Number of items checked.
    /// </summary>
    public int ItemsChecked { get; set; }

    /// <summary>
    /// Number of items with correct formulas.
    /// </summary>
    public int ItemsPassed { get; set; }

    /// <summary>
    /// Number of items with formula errors.
    /// </summary>
    public int ItemsFailed { get; set; }

    /// <summary>
    /// Tolerance percentage used for comparison.
    /// </summary>
    public decimal TolerancePercent { get; set; } = 1.0m;

    /// <summary>
    /// Items with formula errors.
    /// </summary>
    public List<FormulaErrorDto> Errors { get; set; } = new();
}

/// <summary>
/// Details of a formula error.
/// </summary>
public class FormulaErrorDto
{
    /// <summary>
    /// Item identifier.
    /// </summary>
    public Guid ItemId { get; set; }

    /// <summary>
    /// Item number.
    /// </summary>
    public string ItemNumber { get; set; } = string.Empty;

    /// <summary>
    /// Quantity value.
    /// </summary>
    public decimal? Quantity { get; set; }

    /// <summary>
    /// Unit rate value.
    /// </summary>
    public decimal? UnitRate { get; set; }

    /// <summary>
    /// Amount provided by bidder.
    /// </summary>
    public decimal? AmountProvided { get; set; }

    /// <summary>
    /// Amount calculated (Qty x Rate).
    /// </summary>
    public decimal? AmountCalculated { get; set; }

    /// <summary>
    /// Deviation percentage.
    /// </summary>
    public decimal DeviationPercent { get; set; }
}

/// <summary>
/// Data validation results.
/// </summary>
public class DataValidationResultDto
{
    /// <summary>
    /// Number of items with valid data.
    /// </summary>
    public int ValidItems { get; set; }

    /// <summary>
    /// Number of items with negative values.
    /// </summary>
    public int NegativeValueCount { get; set; }

    /// <summary>
    /// Number of items with zero rates.
    /// </summary>
    public int ZeroRateCount { get; set; }

    /// <summary>
    /// Number of items with missing required fields.
    /// </summary>
    public int MissingFieldCount { get; set; }

    /// <summary>
    /// Items with negative values.
    /// </summary>
    public List<Guid> NegativeValueItems { get; set; } = new();

    /// <summary>
    /// Items with zero rates.
    /// </summary>
    public List<Guid> ZeroRateItems { get; set; } = new();
}

/// <summary>
/// Coverage check results.
/// </summary>
public class CoverageCheckResultDto
{
    /// <summary>
    /// Total items in master BOQ.
    /// </summary>
    public int MasterBoqItemCount { get; set; }

    /// <summary>
    /// Number of master items matched.
    /// </summary>
    public int MatchedItemCount { get; set; }

    /// <summary>
    /// Number of master items not matched.
    /// </summary>
    public int UnmatchedMasterItemCount { get; set; }

    /// <summary>
    /// Number of extra items from bidder.
    /// </summary>
    public int ExtraItemCount { get; set; }

    /// <summary>
    /// Coverage percentage.
    /// </summary>
    public decimal CoveragePercent => MasterBoqItemCount > 0
        ? (decimal)MatchedItemCount / MasterBoqItemCount * 100
        : 100m;

    /// <summary>
    /// IDs of unmatched master items.
    /// </summary>
    public List<Guid> UnmatchedMasterItemIds { get; set; } = new();

    /// <summary>
    /// IDs of extra items from bidder.
    /// </summary>
    public List<Guid> ExtraItemIds { get; set; } = new();
}

/// <summary>
/// Outlier detection results.
/// </summary>
public class OutlierDetectionResultDto
{
    /// <summary>
    /// Number of other bids used for comparison.
    /// </summary>
    public int ComparableBidCount { get; set; }

    /// <summary>
    /// Number of potential outliers detected.
    /// </summary>
    public int OutlierCount { get; set; }

    /// <summary>
    /// Number of high outliers (significantly above average).
    /// </summary>
    public int HighOutlierCount { get; set; }

    /// <summary>
    /// Number of low outliers (significantly below average).
    /// </summary>
    public int LowOutlierCount { get; set; }

    /// <summary>
    /// Details of detected outliers.
    /// </summary>
    public List<OutlierItemDto> Outliers { get; set; } = new();
}

/// <summary>
/// Details of an outlier item.
/// </summary>
public class OutlierItemDto
{
    /// <summary>
    /// Item identifier.
    /// </summary>
    public Guid ItemId { get; set; }

    /// <summary>
    /// Item number.
    /// </summary>
    public string ItemNumber { get; set; } = string.Empty;

    /// <summary>
    /// This bid's rate.
    /// </summary>
    public decimal BidRate { get; set; }

    /// <summary>
    /// Average rate from other bids.
    /// </summary>
    public decimal AverageRate { get; set; }

    /// <summary>
    /// Deviation from average percentage.
    /// </summary>
    public decimal DeviationPercent { get; set; }

    /// <summary>
    /// Whether this is a high outlier.
    /// </summary>
    public bool IsHighOutlier { get; set; }
}
