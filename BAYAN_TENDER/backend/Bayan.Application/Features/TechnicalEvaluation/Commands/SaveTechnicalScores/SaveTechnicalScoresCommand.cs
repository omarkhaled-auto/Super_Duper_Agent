using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Commands.SaveTechnicalScores;

/// <summary>
/// Command to save technical scores (draft or final submission).
/// </summary>
public record SaveTechnicalScoresCommand : IRequest<SaveTechnicalScoresResult>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// List of scores to save.
    /// </summary>
    public List<SaveTechnicalScoreDto> Scores { get; init; } = new();

    /// <summary>
    /// Whether to submit final scores (true) or save as draft (false).
    /// Final submission locks the scores from further editing.
    /// </summary>
    public bool IsFinalSubmission { get; init; }
}

/// <summary>
/// Result of SaveTechnicalScoresCommand execution.
/// </summary>
public record SaveTechnicalScoresResult
{
    /// <summary>
    /// Number of scores saved/updated.
    /// </summary>
    public int ScoresSaved { get; init; }

    /// <summary>
    /// Whether the scores were submitted as final.
    /// </summary>
    public bool IsFinalized { get; init; }

    /// <summary>
    /// Whether the save operation was successful.
    /// </summary>
    public bool Success { get; init; }

    /// <summary>
    /// Error message if save failed.
    /// </summary>
    public string? ErrorMessage { get; init; }

    /// <summary>
    /// List of validation errors for individual scores.
    /// </summary>
    public List<ScoreValidationError> ValidationErrors { get; init; } = new();
}

/// <summary>
/// Represents a validation error for a specific score.
/// </summary>
public record ScoreValidationError
{
    /// <summary>
    /// The bidder ID.
    /// </summary>
    public Guid BidderId { get; init; }

    /// <summary>
    /// The criterion ID.
    /// </summary>
    public Guid CriterionId { get; init; }

    /// <summary>
    /// The error message.
    /// </summary>
    public string ErrorMessage { get; init; } = string.Empty;
}
