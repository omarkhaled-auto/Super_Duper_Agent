using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Dashboard.DTOs;

/// <summary>
/// Data transfer object for the Approver dashboard.
/// </summary>
public class ApproverDashboardDto
{
    /// <summary>
    /// Pending approval items for the current user.
    /// </summary>
    public List<PendingApprovalItemDto> PendingApprovals { get; set; } = new();

    /// <summary>
    /// Recent activity/decisions made by the user.
    /// </summary>
    public List<RecentDecisionDto> RecentDecisions { get; set; } = new();

    /// <summary>
    /// Approval statistics for the user.
    /// </summary>
    public ApprovalStatsDto Stats { get; set; } = new();
}

/// <summary>
/// Data transfer object for a pending approval item.
/// </summary>
public class PendingApprovalItemDto
{
    /// <summary>
    /// Approval workflow ID.
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
    /// Client name.
    /// </summary>
    public string ClientName { get; set; } = string.Empty;

    /// <summary>
    /// Estimated tender value.
    /// </summary>
    public decimal? TenderValue { get; set; }

    /// <summary>
    /// Currency code.
    /// </summary>
    public string Currency { get; set; } = string.Empty;

    /// <summary>
    /// Current approval level.
    /// </summary>
    public int CurrentLevel { get; set; }

    /// <summary>
    /// Total approval levels.
    /// </summary>
    public int TotalLevels { get; set; }

    /// <summary>
    /// Name of user who initiated the approval.
    /// </summary>
    public string InitiatedByName { get; set; } = string.Empty;

    /// <summary>
    /// When the approval was submitted/initiated.
    /// </summary>
    public DateTime SubmittedAt { get; set; }

    /// <summary>
    /// Deadline for this approval level.
    /// </summary>
    public DateTime? Deadline { get; set; }

    /// <summary>
    /// Days until deadline (negative if overdue).
    /// </summary>
    public int? DaysUntilDeadline => Deadline.HasValue
        ? (int)(Deadline.Value - DateTime.UtcNow).TotalDays
        : null;

    /// <summary>
    /// Whether the approval is overdue.
    /// </summary>
    public bool IsOverdue => Deadline.HasValue && Deadline.Value < DateTime.UtcNow;

    /// <summary>
    /// Whether the deadline is approaching (within 24 hours).
    /// </summary>
    public bool IsUrgent => Deadline.HasValue && !IsOverdue &&
        (Deadline.Value - DateTime.UtcNow).TotalHours <= 24;
}

/// <summary>
/// Data transfer object for a recent approval decision.
/// </summary>
public class RecentDecisionDto
{
    /// <summary>
    /// Approval level ID.
    /// </summary>
    public Guid Id { get; set; }

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
    /// Decision made.
    /// </summary>
    public ApprovalDecision Decision { get; set; }

    /// <summary>
    /// Human-readable decision text.
    /// </summary>
    public string DecisionText => Decision switch
    {
        ApprovalDecision.Approve => "Approved",
        ApprovalDecision.Reject => "Rejected",
        ApprovalDecision.ReturnForRevision => "Returned",
        _ => "Unknown"
    };

    /// <summary>
    /// Comment provided with the decision.
    /// </summary>
    public string? Comment { get; set; }

    /// <summary>
    /// When the decision was made.
    /// </summary>
    public DateTime DecidedAt { get; set; }
}

/// <summary>
/// Data transfer object for approval statistics.
/// </summary>
public class ApprovalStatsDto
{
    /// <summary>
    /// Total approvals pending for the user.
    /// </summary>
    public int PendingCount { get; set; }

    /// <summary>
    /// Total approvals approved by the user (all time or this month).
    /// </summary>
    public int ApprovedCount { get; set; }

    /// <summary>
    /// Total approvals rejected by the user.
    /// </summary>
    public int RejectedCount { get; set; }

    /// <summary>
    /// Total approvals returned for revision by the user.
    /// </summary>
    public int ReturnedCount { get; set; }

    /// <summary>
    /// Total decisions made this month.
    /// </summary>
    public int TotalThisMonth { get; set; }

    /// <summary>
    /// Average response time in hours.
    /// </summary>
    public decimal? AverageResponseTimeHours { get; set; }
}
