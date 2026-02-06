using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a panelist assigned to evaluate a tender.
/// </summary>
public class EvaluationPanel : BaseEntity
{
    /// <summary>
    /// Tender being evaluated.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// User assigned as panelist.
    /// </summary>
    public Guid PanelistUserId { get; set; }

    /// <summary>
    /// When the panelist was assigned.
    /// </summary>
    public DateTime AssignedAt { get; set; }

    /// <summary>
    /// When the panelist completed their evaluation.
    /// </summary>
    public DateTime? CompletedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this panel assignment.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// User assigned as panelist.
    /// </summary>
    public virtual User Panelist { get; set; } = null!;
}
