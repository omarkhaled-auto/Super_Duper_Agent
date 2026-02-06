using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a level in the approval workflow.
/// </summary>
public class ApprovalLevel : BaseEntity
{
    /// <summary>
    /// Workflow this level belongs to.
    /// </summary>
    public Guid WorkflowId { get; set; }

    /// <summary>
    /// Level number (sequential).
    /// </summary>
    public int LevelNumber { get; set; }

    /// <summary>
    /// User assigned as approver.
    /// </summary>
    public Guid ApproverUserId { get; set; }

    /// <summary>
    /// Deadline for this approval level.
    /// </summary>
    public DateTime? Deadline { get; set; }

    /// <summary>
    /// Decision made at this level.
    /// </summary>
    public ApprovalDecision? Decision { get; set; }

    /// <summary>
    /// Comment on the decision.
    /// </summary>
    public string? DecisionComment { get; set; }

    /// <summary>
    /// When the decision was made.
    /// </summary>
    public DateTime? DecidedAt { get; set; }

    /// <summary>
    /// Current status of this level.
    /// </summary>
    public ApprovalLevelStatus Status { get; set; } = ApprovalLevelStatus.Waiting;

    /// <summary>
    /// When the approver was notified.
    /// </summary>
    public DateTime? NotifiedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Workflow associated with this level.
    /// </summary>
    public virtual ApprovalWorkflow Workflow { get; set; } = null!;

    /// <summary>
    /// User assigned as approver.
    /// </summary>
    public virtual User Approver { get; set; } = null!;
}
