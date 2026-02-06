using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a technical score given by a panelist.
/// </summary>
public class TechnicalScore : BaseEntity
{
    /// <summary>
    /// Tender being evaluated.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder being scored.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Panelist giving the score.
    /// </summary>
    public Guid PanelistUserId { get; set; }

    /// <summary>
    /// Criterion being scored.
    /// </summary>
    public Guid CriterionId { get; set; }

    /// <summary>
    /// Score value (0-10 scale).
    /// </summary>
    public decimal Score { get; set; }

    /// <summary>
    /// Comment/justification for the score.
    /// </summary>
    public string? Comment { get; set; }

    /// <summary>
    /// Whether this is a draft score.
    /// </summary>
    public bool IsDraft { get; set; } = true;

    /// <summary>
    /// When the score was submitted.
    /// </summary>
    public DateTime? SubmittedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this score.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Bidder being scored.
    /// </summary>
    public virtual Bidder Bidder { get; set; } = null!;

    /// <summary>
    /// Panelist giving the score.
    /// </summary>
    public virtual User Panelist { get; set; } = null!;

    /// <summary>
    /// Criterion being scored.
    /// </summary>
    public virtual EvaluationCriteria Criterion { get; set; } = null!;
}
