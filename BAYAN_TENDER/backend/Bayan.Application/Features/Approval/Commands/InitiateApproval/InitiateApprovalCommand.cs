using Bayan.Application.Features.Approval.DTOs;
using MediatR;

namespace Bayan.Application.Features.Approval.Commands.InitiateApproval;

/// <summary>
/// Command to initiate an approval workflow for a tender.
/// </summary>
public record InitiateApprovalCommand : IRequest<InitiateApprovalResult>
{
    /// <summary>
    /// ID of the tender to create approval workflow for.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// Optional path to the award pack PDF in storage.
    /// </summary>
    public string? AwardPackPdfPath { get; init; }

    /// <summary>
    /// List of approver user IDs in sequential order.
    /// Must contain exactly 3 approvers (Level 1, Level 2, Level 3).
    /// </summary>
    public List<Guid> ApproverUserIds { get; init; } = new();

    /// <summary>
    /// Optional deadlines for each approval level.
    /// If not provided, defaults will be used.
    /// </summary>
    public List<DateTime?>? LevelDeadlines { get; init; }

    /// <summary>
    /// Optional reason required when re-initiating with changed approvers.
    /// </summary>
    public string? ApproverChangeReason { get; init; }
}

/// <summary>
/// Result of InitiateApprovalCommand execution.
/// </summary>
public record InitiateApprovalResult
{
    /// <summary>
    /// The ID of the created approval workflow.
    /// </summary>
    public Guid WorkflowId { get; init; }

    /// <summary>
    /// The created approval workflow details.
    /// </summary>
    public ApprovalWorkflowDto Workflow { get; init; } = null!;

    /// <summary>
    /// Whether the Level 1 approver notification email was sent successfully.
    /// </summary>
    public bool Level1NotificationSent { get; init; }
}
