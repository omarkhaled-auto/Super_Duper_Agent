using Bayan.Domain.Enums;

namespace Bayan.Application.Features.TechnicalEvaluation.DTOs;

/// <summary>
/// DTO representing the technical evaluation setup configuration for a tender.
/// </summary>
public class EvaluationSetupDto
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// The tender reference number.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// The scoring method used for technical evaluation.
    /// </summary>
    public ScoringMethod ScoringMethod { get; set; }

    /// <summary>
    /// Whether blind evaluation mode is enabled.
    /// When enabled, panelists cannot see bidder names.
    /// </summary>
    public bool BlindMode { get; set; }

    /// <summary>
    /// Deadline for completing technical evaluation.
    /// </summary>
    public DateTime? TechnicalEvaluationDeadline { get; set; }

    /// <summary>
    /// Whether technical scores are locked.
    /// </summary>
    public bool TechnicalScoresLocked { get; set; }

    /// <summary>
    /// When technical scores were locked.
    /// </summary>
    public DateTime? TechnicalLockedAt { get; set; }

    /// <summary>
    /// Name of the user who locked the scores.
    /// </summary>
    public string? TechnicalLockedByName { get; set; }

    /// <summary>
    /// Weight percentage for technical evaluation (0-100).
    /// </summary>
    public int TechnicalWeight { get; set; }

    /// <summary>
    /// Weight percentage for commercial evaluation (0-100).
    /// </summary>
    public int CommercialWeight { get; set; }

    /// <summary>
    /// List of panelists assigned to this evaluation.
    /// </summary>
    public List<PanelistDto> Panelists { get; set; } = new();

    /// <summary>
    /// List of evaluation criteria for this tender.
    /// </summary>
    public List<EvaluationCriterionInfoDto> Criteria { get; set; } = new();

    /// <summary>
    /// Number of bidders to evaluate.
    /// </summary>
    public int BidderCount { get; set; }

    /// <summary>
    /// Whether the evaluation setup is complete.
    /// </summary>
    public bool IsSetupComplete { get; set; }
}

/// <summary>
/// DTO representing basic evaluation criterion information.
/// </summary>
public class EvaluationCriterionInfoDto
{
    /// <summary>
    /// The criterion's unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Name of the criterion.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Weight percentage for this criterion.
    /// </summary>
    public decimal WeightPercentage { get; set; }

    /// <summary>
    /// Guidance notes for evaluators.
    /// </summary>
    public string? GuidanceNotes { get; set; }

    /// <summary>
    /// Display order.
    /// </summary>
    public int SortOrder { get; set; }
}
