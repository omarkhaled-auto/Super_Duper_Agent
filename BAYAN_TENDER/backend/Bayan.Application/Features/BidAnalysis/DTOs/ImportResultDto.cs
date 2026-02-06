namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Result of bid import execution.
/// </summary>
public class ImportResultDto
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
    /// Bidder identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderCompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Number of items imported.
    /// </summary>
    public int ItemsImported { get; set; }

    /// <summary>
    /// Number of items updated (if re-import).
    /// </summary>
    public int ItemsUpdated { get; set; }

    /// <summary>
    /// Number of items skipped.
    /// </summary>
    public int ItemsSkipped { get; set; }

    /// <summary>
    /// Total amount in native currency.
    /// </summary>
    public decimal TotalAmount { get; set; }

    /// <summary>
    /// Native currency code.
    /// </summary>
    public string NativeCurrency { get; set; } = string.Empty;

    /// <summary>
    /// Normalized total amount in base currency.
    /// </summary>
    public decimal NormalizedTotal { get; set; }

    /// <summary>
    /// Base currency code.
    /// </summary>
    public string BaseCurrency { get; set; } = "AED";

    /// <summary>
    /// Exchange rate applied.
    /// </summary>
    public decimal FxRate { get; set; } = 1.0m;

    /// <summary>
    /// Import status.
    /// </summary>
    public ImportStatus Status { get; set; }

    /// <summary>
    /// Import status display name.
    /// </summary>
    public string StatusName => Status.ToString();

    /// <summary>
    /// When the import was executed.
    /// </summary>
    public DateTime ImportedAt { get; set; }

    /// <summary>
    /// User who performed the import.
    /// </summary>
    public Guid? ImportedBy { get; set; }

    /// <summary>
    /// Vendor pricing snapshot ID if created.
    /// </summary>
    public Guid? VendorPricingSnapshotId { get; set; }

    /// <summary>
    /// Summary of validation performed before import.
    /// </summary>
    public ValidationSummaryDto? ValidationSummary { get; set; }

    /// <summary>
    /// Any warnings from the import process.
    /// </summary>
    public List<string> Warnings { get; set; } = new();

    /// <summary>
    /// Whether the import was successful.
    /// </summary>
    public bool IsSuccess => Status == ImportStatus.Imported;
}

/// <summary>
/// Import status for the result.
/// </summary>
public enum ImportStatus
{
    /// <summary>
    /// Import completed successfully.
    /// </summary>
    Imported = 0,

    /// <summary>
    /// Import completed with warnings.
    /// </summary>
    ImportedWithWarnings = 1,

    /// <summary>
    /// Import partially completed.
    /// </summary>
    PartiallyImported = 2,

    /// <summary>
    /// Import failed.
    /// </summary>
    Failed = 3
}

/// <summary>
/// Summary of validation for the import result.
/// </summary>
public class ValidationSummaryDto
{
    /// <summary>
    /// Total items validated.
    /// </summary>
    public int TotalItems { get; set; }

    /// <summary>
    /// Items that passed validation.
    /// </summary>
    public int ValidItems { get; set; }

    /// <summary>
    /// Items with warnings.
    /// </summary>
    public int WarningItems { get; set; }

    /// <summary>
    /// Items with formula errors.
    /// </summary>
    public int FormulaErrorCount { get; set; }

    /// <summary>
    /// Non-comparable items count.
    /// </summary>
    public int NonComparableCount { get; set; }

    /// <summary>
    /// BOQ coverage percentage.
    /// </summary>
    public decimal CoveragePercent { get; set; }
}
