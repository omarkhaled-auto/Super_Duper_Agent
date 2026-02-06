using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Approval.DTOs;

/// <summary>
/// Data transfer object for approval level.
/// </summary>
public class ApprovalLevelDto
{
    /// <summary>
    /// Level ID.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Workflow ID this level belongs to.
    /// </summary>
    public Guid WorkflowId { get; set; }

    /// <summary>
    /// Sequential level number (1, 2, 3).
    /// </summary>
    public int LevelNumber { get; set; }

    /// <summary>
    /// User ID of the approver.
    /// </summary>
    public Guid ApproverUserId { get; set; }

    /// <summary>
    /// Name of the approver.
    /// </summary>
    public string ApproverName { get; set; } = string.Empty;

    /// <summary>
    /// Email of the approver.
    /// </summary>
    public string ApproverEmail { get; set; } = string.Empty;

    /// <summary>
    /// Deadline for this approval level.
    /// </summary>
    public DateTime? Deadline { get; set; }

    /// <summary>
    /// Decision made at this level (null if pending).
    /// </summary>
    public ApprovalDecision? Decision { get; set; }

    /// <summary>
    /// Comment provided with the decision.
    /// </summary>
    public string? DecisionComment { get; set; }

    /// <summary>
    /// When the decision was made.
    /// </summary>
    public DateTime? DecidedAt { get; set; }

    /// <summary>
    /// Current status of this level.
    /// </summary>
    public ApprovalLevelStatus Status { get; set; }

    /// <summary>
    /// When the approver was notified.
    /// </summary>
    public DateTime? NotifiedAt { get; set; }

    /// <summary>
    /// Whether this level is currently active and awaiting decision.
    /// </summary>
    public bool IsActive => Status == ApprovalLevelStatus.Active;
}
