namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// DTO for import validation results.
/// </summary>
public record ImportValidationResultDto
{
    /// <summary>
    /// The import session ID.
    /// </summary>
    public Guid ImportSessionId { get; init; }

    /// <summary>
    /// Number of rows that passed validation.
    /// </summary>
    public int ValidCount { get; init; }

    /// <summary>
    /// Number of rows with warnings (can still be imported).
    /// </summary>
    public int WarningCount { get; init; }

    /// <summary>
    /// Number of rows with errors (cannot be imported).
    /// </summary>
    public int ErrorCount { get; init; }

    /// <summary>
    /// Total number of rows processed.
    /// </summary>
    public int TotalRows { get; init; }

    /// <summary>
    /// Whether the import can proceed.
    /// </summary>
    public bool CanProceed => ErrorCount == 0;

    /// <summary>
    /// List of validation issues.
    /// </summary>
    public List<ImportValidationIssue> Issues { get; init; } = new();

    /// <summary>
    /// Detected sections from item number parsing.
    /// </summary>
    public List<DetectedSectionDto> DetectedSections { get; init; } = new();

    /// <summary>
    /// Summary of detected data.
    /// </summary>
    public ImportDataSummary Summary { get; init; } = new();
}

/// <summary>
/// Represents a single validation issue.
/// </summary>
public record ImportValidationIssue
{
    /// <summary>
    /// Row number in the Excel file (1-based for user display).
    /// </summary>
    public int RowNumber { get; init; }

    /// <summary>
    /// Column name where the issue occurred.
    /// </summary>
    public string? ColumnName { get; init; }

    /// <summary>
    /// The problematic value.
    /// </summary>
    public string? Value { get; init; }

    /// <summary>
    /// Issue severity.
    /// </summary>
    public ValidationSeverity Severity { get; init; }

    /// <summary>
    /// Issue code for programmatic handling.
    /// </summary>
    public string IssueCode { get; init; } = string.Empty;

    /// <summary>
    /// Human-readable message describing the issue.
    /// </summary>
    public string Message { get; init; } = string.Empty;

    /// <summary>
    /// Suggested fix for the issue.
    /// </summary>
    public string? SuggestedFix { get; init; }
}

/// <summary>
/// Validation issue severity levels.
/// </summary>
public enum ValidationSeverity
{
    /// <summary>
    /// Information only, no action needed.
    /// </summary>
    Info = 0,

    /// <summary>
    /// Warning - row can be imported but may have issues.
    /// </summary>
    Warning = 1,

    /// <summary>
    /// Error - row cannot be imported.
    /// </summary>
    Error = 2
}

/// <summary>
/// DTO for a detected section from item numbers.
/// </summary>
public record DetectedSectionDto
{
    /// <summary>
    /// Section number (e.g., "1", "1.2").
    /// </summary>
    public string SectionNumber { get; init; } = string.Empty;

    /// <summary>
    /// Detected or default section title.
    /// </summary>
    public string Title { get; init; } = string.Empty;

    /// <summary>
    /// Number of items that will be placed in this section.
    /// </summary>
    public int ItemCount { get; init; }

    /// <summary>
    /// Parent section number (null for top-level sections).
    /// </summary>
    public string? ParentSectionNumber { get; init; }

    /// <summary>
    /// Nesting level (0 for top-level sections).
    /// </summary>
    public int Level { get; init; }
}

/// <summary>
/// Summary of import data.
/// </summary>
public record ImportDataSummary
{
    /// <summary>
    /// Total number of sections to be created.
    /// </summary>
    public int TotalSections { get; init; }

    /// <summary>
    /// Total number of items to be imported.
    /// </summary>
    public int TotalItems { get; init; }

    /// <summary>
    /// Number of unique UOM codes found.
    /// </summary>
    public int UniqueUomCount { get; init; }

    /// <summary>
    /// List of UOM codes found in the file.
    /// </summary>
    public List<string> UomCodes { get; init; } = new();

    /// <summary>
    /// UOM codes that don't exist in the master list.
    /// </summary>
    public List<string> UnknownUomCodes { get; init; } = new();

    /// <summary>
    /// Number of rows that will be skipped (empty or invalid).
    /// </summary>
    public int SkippedRows { get; init; }
}

/// <summary>
/// Common validation issue codes.
/// </summary>
public static class ValidationIssueCodes
{
    public const string MissingItemNumber = "MISSING_ITEM_NUMBER";
    public const string MissingDescription = "MISSING_DESCRIPTION";
    public const string InvalidItemNumber = "INVALID_ITEM_NUMBER";
    public const string InvalidQuantity = "INVALID_QUANTITY";
    public const string UnknownUom = "UNKNOWN_UOM";
    public const string DuplicateItemNumber = "DUPLICATE_ITEM_NUMBER";
    public const string EmptyRow = "EMPTY_ROW";
    public const string OrphanItem = "ORPHAN_ITEM";
    public const string NegativeQuantity = "NEGATIVE_QUANTITY";
}
