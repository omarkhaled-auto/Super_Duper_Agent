using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a user's notification preferences.
/// </summary>
public class NotificationPreference : BaseEntity
{
    /// <summary>
    /// User these preferences belong to.
    /// </summary>
    public Guid UserId { get; set; }

    /// <summary>
    /// Receive tender invitation notifications.
    /// </summary>
    public bool TenderInvitation { get; set; } = true;

    /// <summary>
    /// Receive addendum issued notifications.
    /// </summary>
    public bool AddendumIssued { get; set; } = true;

    /// <summary>
    /// Receive clarification published notifications.
    /// </summary>
    public bool ClarificationPublished { get; set; } = true;

    /// <summary>
    /// Receive 3-day deadline reminders.
    /// </summary>
    public bool DeadlineReminder3Days { get; set; } = true;

    /// <summary>
    /// Receive 1-day deadline reminders.
    /// </summary>
    public bool DeadlineReminder1Day { get; set; } = true;

    /// <summary>
    /// Receive approval request notifications.
    /// </summary>
    public bool ApprovalRequest { get; set; } = true;

    // Navigation properties
    /// <summary>
    /// User associated with these preferences.
    /// </summary>
    public virtual User User { get; set; } = null!;
}
