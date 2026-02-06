namespace Bayan.Application.Features.Tenders.DTOs;

/// <summary>
/// Data transfer object for tender activity/audit log entry.
/// </summary>
public class TenderActivityDto
{
    /// <summary>
    /// Activity type/action performed.
    /// </summary>
    public string ActivityType { get; set; } = string.Empty;

    /// <summary>
    /// Description of the activity.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// User who performed the activity.
    /// </summary>
    public string? PerformedBy { get; set; }

    /// <summary>
    /// User ID who performed the activity.
    /// </summary>
    public Guid? PerformedById { get; set; }

    /// <summary>
    /// When the activity occurred.
    /// </summary>
    public DateTime OccurredAt { get; set; }

    /// <summary>
    /// Additional details or metadata about the activity.
    /// </summary>
    public string? Details { get; set; }
}
