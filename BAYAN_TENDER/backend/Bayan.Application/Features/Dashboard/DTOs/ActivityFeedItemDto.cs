namespace Bayan.Application.Features.Dashboard.DTOs;

/// <summary>
/// Data transfer object for an activity feed item.
/// </summary>
public class ActivityFeedItemDto
{
    /// <summary>
    /// Activity ID.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Type of activity (e.g., "TenderCreated", "BidReceived", "ApprovalCompleted").
    /// </summary>
    public string ActivityType { get; set; } = string.Empty;

    /// <summary>
    /// Human-readable description of the activity.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Associated entity type (e.g., "Tender", "Bid", "Approval").
    /// </summary>
    public string EntityType { get; set; } = string.Empty;

    /// <summary>
    /// ID of the associated entity.
    /// </summary>
    public Guid? EntityId { get; set; }

    /// <summary>
    /// User who performed the activity.
    /// </summary>
    public string? PerformedBy { get; set; }

    /// <summary>
    /// When the activity occurred.
    /// </summary>
    public DateTime OccurredAt { get; set; }

    /// <summary>
    /// Icon class for the activity type.
    /// </summary>
    public string Icon { get; set; } = string.Empty;

    /// <summary>
    /// Color theme for the activity type.
    /// </summary>
    public string Color { get; set; } = string.Empty;
}
