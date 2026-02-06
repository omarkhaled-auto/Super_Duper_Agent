using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents an approval workflow for a tender.
/// </summary>
public class ApprovalWorkflow : BaseEntity
{
    /// <summary>
    /// Tender this workflow is for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Current status of the workflow.
    /// </summary>
    public ApprovalWorkflowStatus Status { get; set; } = ApprovalWorkflowStatus.Pending;

    /// <summary>
    /// User who initiated the workflow.
    /// </summary>
    public Guid InitiatedBy { get; set; }

    /// <summary>
    /// When the workflow was initiated.
    /// </summary>
    public DateTime InitiatedAt { get; set; }

    /// <summary>
    /// When the workflow was completed.
    /// </summary>
    public DateTime? CompletedAt { get; set; }

    /// <summary>
    /// Path to award pack PDF in MinIO.
    /// </summary>
    public string? AwardPackPdfPath { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this workflow.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// User who initiated the workflow.
    /// </summary>
    public virtual User Initiator { get; set; } = null!;

    /// <summary>
    /// Approval levels in this workflow.
    /// </summary>
    public virtual ICollection<ApprovalLevel> Levels { get; set; } = new List<ApprovalLevel>();
}
