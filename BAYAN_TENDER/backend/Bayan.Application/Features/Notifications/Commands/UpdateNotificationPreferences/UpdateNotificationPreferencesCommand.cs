namespace Bayan.Application.Features.Notifications.Commands.UpdateNotificationPreferences;

using Bayan.Application.Features.Notifications.DTOs;
using MediatR;

/// <summary>
/// Command to update the current user's notification preferences.
/// </summary>
public record UpdateNotificationPreferencesCommand : IRequest<NotificationPreferencesDto>
{
    /// <summary>
    /// Receive tender invitation notifications.
    /// </summary>
    public bool TenderInvitation { get; init; } = true;

    /// <summary>
    /// Receive addendum issued notifications.
    /// </summary>
    public bool AddendumIssued { get; init; } = true;

    /// <summary>
    /// Receive clarification published notifications.
    /// </summary>
    public bool ClarificationPublished { get; init; } = true;

    /// <summary>
    /// Receive 3-day deadline reminders.
    /// </summary>
    public bool DeadlineReminder3Days { get; init; } = true;

    /// <summary>
    /// Receive 1-day deadline reminders.
    /// </summary>
    public bool DeadlineReminder1Day { get; init; } = true;

    /// <summary>
    /// Receive approval request notifications.
    /// </summary>
    public bool ApprovalRequest { get; init; } = true;
}
