using Bayan.Application.Features.Approval.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Approval.Commands.SubmitApprovalDecision;

/// <summary>
/// Command to submit an approval decision for a tender.
/// </summary>
public record SubmitApprovalDecisionCommand : IRequest<SubmitApprovalDecisionResult>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// The decision being made (Approve, Reject, ReturnForRevision).
    /// </summary>
    public ApprovalDecision Decision { get; init; }

    /// <summary>
    /// Comment explaining the decision.
    /// Required for Reject and ReturnForRevision decisions.
    /// </summary>
    public string? Comment { get; init; }
}

/// <summary>
/// Result of SubmitApprovalDecisionCommand execution.
/// </summary>
public record SubmitApprovalDecisionResult
{
    /// <summary>
    /// Whether the decision was successfully recorded.
    /// </summary>
    public bool Success { get; init; }

    /// <summary>
    /// The updated approval workflow.
    /// </summary>
    public ApprovalWorkflowDto Workflow { get; init; } = null!;

    /// <summary>
    /// Message describing the result.
    /// </summary>
    public string Message { get; init; } = string.Empty;

    /// <summary>
    /// Whether this was the final approval (workflow completed).
    /// </summary>
    public bool IsWorkflowComplete { get; init; }

    /// <summary>
    /// Whether notification was sent successfully.
    /// </summary>
    public bool NotificationSent { get; init; }
}
