using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Approval.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Approval.Queries.GetApprovalStatus;

/// <summary>
/// Handler for GetApprovalStatusQuery.
/// </summary>
public class GetApprovalStatusQueryHandler : IRequestHandler<GetApprovalStatusQuery, ApprovalWorkflowDto?>
{
    private readonly IApplicationDbContext _context;

    public GetApprovalStatusQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<ApprovalWorkflowDto?> Handle(GetApprovalStatusQuery request, CancellationToken cancellationToken)
    {
        var workflow = await _context.ApprovalWorkflows
            .Include(w => w.Levels)
            .Include(w => w.Tender)
            .Include(w => w.Initiator)
            .FirstOrDefaultAsync(w => w.TenderId == request.TenderId, cancellationToken);

        if (workflow == null)
            return null;

        // Get approver users
        var approverUserIds = workflow.Levels.Select(l => l.ApproverUserId).ToList();
        var approverUsers = await _context.Users
            .Where(u => approverUserIds.Contains(u.Id))
            .ToDictionaryAsync(u => u.Id, cancellationToken);

        // Determine current active level
        var currentLevel = workflow.Levels
            .OrderBy(l => l.LevelNumber)
            .FirstOrDefault(l => l.Status == ApprovalLevelStatus.Active)?.LevelNumber ??
            (workflow.Status == ApprovalWorkflowStatus.Approved ? workflow.Levels.Max(l => l.LevelNumber) : 0);

        return new ApprovalWorkflowDto
        {
            Id = workflow.Id,
            TenderId = workflow.TenderId,
            TenderReference = workflow.Tender.Reference,
            TenderTitle = workflow.Tender.Title,
            Status = workflow.Status,
            InitiatedBy = workflow.InitiatedBy,
            InitiatedByName = workflow.Initiator.FullName,
            InitiatedAt = workflow.InitiatedAt,
            CompletedAt = workflow.CompletedAt,
            AwardPackPdfPath = workflow.AwardPackPdfPath,
            CurrentLevel = currentLevel,
            TotalLevels = workflow.Levels.Count,
            Levels = workflow.Levels
                .OrderBy(l => l.LevelNumber)
                .Select(l => new ApprovalLevelDto
                {
                    Id = l.Id,
                    WorkflowId = l.WorkflowId,
                    LevelNumber = l.LevelNumber,
                    ApproverUserId = l.ApproverUserId,
                    ApproverName = approverUsers.TryGetValue(l.ApproverUserId, out var user) ? user.FullName : "Unknown",
                    ApproverEmail = approverUsers.TryGetValue(l.ApproverUserId, out user) ? user.Email : "Unknown",
                    Deadline = l.Deadline,
                    Decision = l.Decision,
                    DecisionComment = l.DecisionComment,
                    DecidedAt = l.DecidedAt,
                    Status = l.Status,
                    NotifiedAt = l.NotifiedAt
                }).ToList()
        };
    }
}
