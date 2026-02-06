using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Commands.LockTechnicalScores;

/// <summary>
/// Command to lock technical scores for a tender.
/// This is an irreversible action that prevents further score modifications.
/// </summary>
public record LockTechnicalScoresCommand : IRequest<LockTechnicalScoresResult>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// Optional confirmation flag to prevent accidental locks.
    /// Must be true to proceed with locking.
    /// </summary>
    public bool Confirm { get; init; }
}

/// <summary>
/// Result of LockTechnicalScoresCommand execution.
/// </summary>
public record LockTechnicalScoresResult
{
    /// <summary>
    /// The tender ID.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// When the scores were locked.
    /// </summary>
    public DateTime? LockedAt { get; init; }

    /// <summary>
    /// Name of the user who locked the scores.
    /// </summary>
    public string? LockedByName { get; init; }

    /// <summary>
    /// Whether the lock operation was successful.
    /// </summary>
    public bool Success { get; init; }

    /// <summary>
    /// Error message if lock failed.
    /// </summary>
    public string? ErrorMessage { get; init; }

    /// <summary>
    /// Number of panelists who have not completed scoring (warning).
    /// </summary>
    public int IncompletePanelistCount { get; init; }

    /// <summary>
    /// Number of bidders without complete scores (warning).
    /// </summary>
    public int IncompleteBidderCount { get; init; }
}
