using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Approval.DTOs;

/// <summary>
/// Data transfer object for submitting an approval decision.
/// </summary>
public class ApprovalDecisionDto
{
    /// <summary>
    /// The decision being made.
    /// </summary>
    public ApprovalDecision Decision { get; set; }

    /// <summary>
    /// Comment explaining the decision.
    /// Required for Reject and ReturnForRevision decisions.
    /// </summary>
    public string? Comment { get; set; }
}
