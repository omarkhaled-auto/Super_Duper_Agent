namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Represents a single validation issue found during bid import validation.
/// </summary>
public class ValidationIssueDto
{
    /// <summary>
    /// Severity level of the issue.
    /// </summary>
    public ValidationIssueSeverity Severity { get; set; }

    /// <summary>
    /// Issue code for programmatic handling.
    /// </summary>
    public string Code { get; set; } = string.Empty;

    /// <summary>
    /// Human-readable description of the issue.
    /// </summary>
    public string Message { get; set; } = string.Empty;

    /// <summary>
    /// Bid pricing item ID if issue is item-specific.
    /// </summary>
    public Guid? ItemId { get; set; }

    /// <summary>
    /// Item number if applicable.
    /// </summary>
    public string? ItemNumber { get; set; }

    /// <summary>
    /// Field name that has the issue.
    /// </summary>
    public string? Field { get; set; }

    /// <summary>
    /// Expected value or format.
    /// </summary>
    public string? ExpectedValue { get; set; }

    /// <summary>
    /// Actual value found.
    /// </summary>
    public string? ActualValue { get; set; }

    /// <summary>
    /// Whether this issue can be auto-corrected.
    /// </summary>
    public bool CanAutoCorrect { get; set; }

    /// <summary>
    /// Suggested correction if available.
    /// </summary>
    public string? SuggestedCorrection { get; set; }
}

/// <summary>
/// Severity levels for validation issues.
/// </summary>
public enum ValidationIssueSeverity
{
    /// <summary>
    /// Informational note, does not block import.
    /// </summary>
    Info = 0,

    /// <summary>
    /// Warning that should be reviewed but doesn't block import.
    /// </summary>
    Warning = 1,

    /// <summary>
    /// Error that blocks import.
    /// </summary>
    Error = 2
}
