using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Approval.DTOs;

/// <summary>
/// Data transfer object for a pending approval item.
/// Used for dashboard display of approvals awaiting user action.
/// </summary>
public class PendingApprovalDto
{
    /// <summary>
    /// Workflow ID.
    /// </summary>
    public Guid WorkflowId { get; set; }

    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender reference number.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Client name for the tender.
    /// </summary>
    public string ClientName { get; set; } = string.Empty;

    /// <summary>
    /// Current level number awaiting approval.
    /// </summary>
    public int LevelNumber { get; set; }

    /// <summary>
    /// Total number of levels in the workflow.
    /// </summary>
    public int TotalLevels { get; set; }

    /// <summary>
    /// Name of the user who initiated the workflow.
    /// </summary>
    public string InitiatedByName { get; set; } = string.Empty;

    /// <summary>
    /// When the workflow was initiated.
    /// </summary>
    public DateTime InitiatedAt { get; set; }

    /// <summary>
    /// When this level was notified.
    /// </summary>
    public DateTime? NotifiedAt { get; set; }

    /// <summary>
    /// Deadline for this approval level.
    /// </summary>
    public DateTime? Deadline { get; set; }

    /// <summary>
    /// Whether the approval is overdue.
    /// </summary>
    public bool IsOverdue => Deadline.HasValue && Deadline.Value < DateTime.UtcNow;

    /// <summary>
    /// Days until deadline (negative if overdue).
    /// </summary>
    public int? DaysUntilDeadline => Deadline.HasValue
        ? (int)(Deadline.Value - DateTime.UtcNow).TotalDays
        : null;

    /// <summary>
    /// Current workflow status.
    /// </summary>
    public ApprovalWorkflowStatus WorkflowStatus { get; set; }
}
