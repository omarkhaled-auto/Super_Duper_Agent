using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Commands.SetupTechnicalEvaluation;

/// <summary>
/// Command to set up technical evaluation for a tender.
/// Creates EvaluationState record and EvaluationPanel records for panelists.
/// </summary>
public record SetupTechnicalEvaluationCommand : IRequest<SetupTechnicalEvaluationResult>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// The scoring method to use.
    /// </summary>
    public ScoringMethod ScoringMethod { get; init; } = ScoringMethod.Numeric;

    /// <summary>
    /// Whether blind evaluation mode is enabled.
    /// When enabled, panelists cannot see bidder names.
    /// </summary>
    public bool BlindMode { get; init; } = true;

    /// <summary>
    /// Deadline for completing technical evaluation.
    /// </summary>
    public DateTime? TechnicalEvaluationDeadline { get; init; }

    /// <summary>
    /// List of user IDs to assign as panelists.
    /// </summary>
    public List<Guid> PanelistUserIds { get; init; } = new();

    /// <summary>
    /// Whether to send notification emails to panelists.
    /// </summary>
    public bool SendNotificationEmails { get; init; } = true;
}

/// <summary>
/// Result of SetupTechnicalEvaluationCommand execution.
/// </summary>
public record SetupTechnicalEvaluationResult
{
    /// <summary>
    /// The evaluation state record ID.
    /// </summary>
    public Guid EvaluationStateId { get; init; }

    /// <summary>
    /// The tender ID.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// Number of panelists assigned.
    /// </summary>
    public int PanelistsAssigned { get; init; }

    /// <summary>
    /// Number of notification emails sent.
    /// </summary>
    public int NotificationsSent { get; init; }

    /// <summary>
    /// Any panelists for whom email failed to send.
    /// </summary>
    public List<string> FailedNotifications { get; init; } = new();

    /// <summary>
    /// Whether setup was successful.
    /// </summary>
    public bool Success { get; init; }

    /// <summary>
    /// Error message if setup failed.
    /// </summary>
    public string? ErrorMessage { get; init; }
}
