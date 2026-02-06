using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents the evaluation state for a tender.
/// </summary>
public class EvaluationState : BaseEntity
{
    /// <summary>
    /// Tender this state belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Scoring method used.
    /// </summary>
    public ScoringMethod ScoringMethod { get; set; } = ScoringMethod.Numeric;

    /// <summary>
    /// Whether blind mode is enabled.
    /// </summary>
    public bool BlindMode { get; set; } = true;

    /// <summary>
    /// Deadline for technical evaluation.
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
    /// User who locked technical scores.
    /// </summary>
    public Guid? TechnicalLockedBy { get; set; }

    /// <summary>
    /// Whether commercial scores have been calculated.
    /// </summary>
    public bool CommercialScoresCalculated { get; set; }

    /// <summary>
    /// Whether combined scores have been calculated.
    /// </summary>
    public bool CombinedScoresCalculated { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this evaluation state.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// User who locked technical scores.
    /// </summary>
    public virtual User? LockedByUser { get; set; }
}
