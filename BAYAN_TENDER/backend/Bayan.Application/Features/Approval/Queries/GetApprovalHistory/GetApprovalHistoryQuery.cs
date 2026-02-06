using Bayan.Application.Features.Approval.DTOs;
using MediatR;

namespace Bayan.Application.Features.Approval.Queries.GetApprovalHistory;

/// <summary>
/// Query to get the approval history for a tender.
/// </summary>
public record GetApprovalHistoryQuery : IRequest<List<ApprovalHistoryDto>>
{
    /// <summary>
    /// ID of the tender to get approval history for.
    /// </summary>
    public Guid TenderId { get; init; }

    public GetApprovalHistoryQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
