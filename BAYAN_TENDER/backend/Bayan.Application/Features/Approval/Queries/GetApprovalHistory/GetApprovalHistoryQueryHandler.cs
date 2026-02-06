using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Approval.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Approval.Queries.GetApprovalHistory;

/// <summary>
/// Handler for GetApprovalHistoryQuery.
/// </summary>
public class GetApprovalHistoryQueryHandler : IRequestHandler<GetApprovalHistoryQuery, List<ApprovalHistoryDto>>
{
    private readonly IApplicationDbContext _context;

    public GetApprovalHistoryQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<ApprovalHistoryDto>> Handle(GetApprovalHistoryQuery request, CancellationToken cancellationToken)
    {
        var workflow = await _context.ApprovalWorkflows
            .Include(w => w.Levels)
            .FirstOrDefaultAsync(w => w.TenderId == request.TenderId, cancellationToken);

        if (workflow == null)
            return new List<ApprovalHistoryDto>();

        // Get approver users
        var approverUserIds = workflow.Levels.Select(l => l.ApproverUserId).ToList();
        var approverUsers = await _context.Users
            .Where(u => approverUserIds.Contains(u.Id))
            .ToDictionaryAsync(u => u.Id, cancellationToken);

        return workflow.Levels
            .OrderBy(l => l.LevelNumber)
            .Select(l => new ApprovalHistoryDto
            {
                Id = l.Id,
                LevelNumber = l.LevelNumber,
                ApproverName = approverUsers.TryGetValue(l.ApproverUserId, out var user) ? user.FullName : "Unknown",
                ApproverEmail = approverUsers.TryGetValue(l.ApproverUserId, out user) ? user.Email : "Unknown",
                ApproverJobTitle = approverUsers.TryGetValue(l.ApproverUserId, out user) ? user.JobTitle : null,
                Decision = l.Decision,
                DecisionComment = l.DecisionComment,
                DecidedAt = l.DecidedAt,
                NotifiedAt = l.NotifiedAt,
                Status = l.Status
            })
            .ToList();
    }
}
