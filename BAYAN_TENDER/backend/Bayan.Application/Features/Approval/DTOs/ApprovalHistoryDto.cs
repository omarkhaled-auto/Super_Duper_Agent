using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Approval.DTOs;

/// <summary>
/// Data transfer object for approval history entry.
/// </summary>
public class ApprovalHistoryDto
{
    /// <summary>
    /// Level ID.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Sequential level number.
    /// </summary>
    public int LevelNumber { get; set; }

    /// <summary>
    /// Name of the approver.
    /// </summary>
    public string ApproverName { get; set; } = string.Empty;

    /// <summary>
    /// Email of the approver.
    /// </summary>
    public string ApproverEmail { get; set; } = string.Empty;

    /// <summary>
    /// Job title of the approver.
    /// </summary>
    public string? ApproverJobTitle { get; set; }

    /// <summary>
    /// Decision made at this level.
    /// </summary>
    public ApprovalDecision? Decision { get; set; }

    /// <summary>
    /// Human-readable decision string.
    /// </summary>
    public string DecisionText => Decision switch
    {
        ApprovalDecision.Approve => "Approved",
        ApprovalDecision.Reject => "Rejected",
        ApprovalDecision.ReturnForRevision => "Returned for Revision",
        null => "Pending",
        _ => "Unknown"
    };

    /// <summary>
    /// Comment provided with the decision.
    /// </summary>
    public string? DecisionComment { get; set; }

    /// <summary>
    /// When the decision was made.
    /// </summary>
    public DateTime? DecidedAt { get; set; }

    /// <summary>
    /// When the approver was notified.
    /// </summary>
    public DateTime? NotifiedAt { get; set; }

    /// <summary>
    /// Current status of this level.
    /// </summary>
    public ApprovalLevelStatus Status { get; set; }

    /// <summary>
    /// Human-readable status string.
    /// </summary>
    public string StatusText => Status switch
    {
        ApprovalLevelStatus.Waiting => "Waiting",
        ApprovalLevelStatus.Active => "Pending Decision",
        ApprovalLevelStatus.Approved => "Approved",
        ApprovalLevelStatus.Rejected => "Rejected",
        ApprovalLevelStatus.Returned => "Returned for Revision",
        _ => "Unknown"
    };
}
