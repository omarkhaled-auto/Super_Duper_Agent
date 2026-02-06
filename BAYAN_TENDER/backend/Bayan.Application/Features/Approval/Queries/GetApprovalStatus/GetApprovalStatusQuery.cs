using Bayan.Application.Features.Approval.DTOs;
using MediatR;

namespace Bayan.Application.Features.Approval.Queries.GetApprovalStatus;

/// <summary>
/// Query to get the current approval status for a tender.
/// </summary>
public record GetApprovalStatusQuery : IRequest<ApprovalWorkflowDto?>
{
    /// <summary>
    /// ID of the tender to get approval status for.
    /// </summary>
    public Guid TenderId { get; init; }

    public GetApprovalStatusQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
