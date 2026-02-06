using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Dashboard.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Dashboard.Queries.GetApproverDashboard;

/// <summary>
/// Handler for the GetApproverDashboardQuery.
/// </summary>
public class GetApproverDashboardQueryHandler
    : IRequestHandler<GetApproverDashboardQuery, ApproverDashboardDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public GetApproverDashboardQueryHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<ApproverDashboardDto> Handle(
        GetApproverDashboardQuery request,
        CancellationToken cancellationToken)
    {
        var currentUserId = _currentUserService.UserId;

        if (!currentUserId.HasValue)
        {
            return new ApproverDashboardDto();
        }

        var pendingApprovals = await GetPendingApprovalsAsync(currentUserId.Value, cancellationToken);
        var recentDecisions = await GetRecentDecisionsAsync(
            currentUserId.Value, request.RecentDecisionsLimit, cancellationToken);
        var stats = await GetApprovalStatsAsync(currentUserId.Value, cancellationToken);

        return new ApproverDashboardDto
        {
            PendingApprovals = pendingApprovals,
            RecentDecisions = recentDecisions,
            Stats = stats
        };
    }

    private async Task<List<PendingApprovalItemDto>> GetPendingApprovalsAsync(
        Guid userId,
        CancellationToken cancellationToken)
    {
        // Get approval levels where the current user is the approver and status is Active
        return await _context.ApprovalLevels
            .Include(al => al.Workflow)
                .ThenInclude(aw => aw.Tender)
                    .ThenInclude(t => t.Client)
            .Include(al => al.Workflow)
                .ThenInclude(aw => aw.Initiator)
            .Where(al => al.ApproverUserId == userId &&
                        al.Status == ApprovalLevelStatus.Active &&
                        al.Workflow.Status == ApprovalWorkflowStatus.InProgress)
            .OrderBy(al => al.Deadline ?? DateTime.MaxValue)
            .Select(al => new PendingApprovalItemDto
            {
                WorkflowId = al.WorkflowId,
                TenderId = al.Workflow.TenderId,
                TenderReference = al.Workflow.Tender.Reference,
                TenderTitle = al.Workflow.Tender.Title,
                ClientName = al.Workflow.Tender.Client.Name,
                TenderValue = null, // Could be added if tender has estimated value field
                Currency = al.Workflow.Tender.BaseCurrency,
                CurrentLevel = al.LevelNumber,
                TotalLevels = al.Workflow.Levels.Count,
                InitiatedByName = al.Workflow.Initiator != null
                    ? $"{al.Workflow.Initiator.FirstName} {al.Workflow.Initiator.LastName}"
                    : "Unknown",
                SubmittedAt = al.Workflow.CreatedAt,
                Deadline = al.Deadline
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);
    }

    private async Task<List<RecentDecisionDto>> GetRecentDecisionsAsync(
        Guid userId,
        int limit,
        CancellationToken cancellationToken)
    {
        return await _context.ApprovalLevels
            .Include(al => al.Workflow)
                .ThenInclude(aw => aw.Tender)
            .Where(al => al.ApproverUserId == userId &&
                        al.Decision.HasValue &&
                        al.DecidedAt.HasValue)
            .OrderByDescending(al => al.DecidedAt)
            .Take(limit)
            .Select(al => new RecentDecisionDto
            {
                Id = al.Id,
                TenderId = al.Workflow.TenderId,
                TenderReference = al.Workflow.Tender.Reference,
                TenderTitle = al.Workflow.Tender.Title,
                Decision = al.Decision!.Value,
                Comment = al.DecisionComment,
                DecidedAt = al.DecidedAt!.Value
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);
    }

    private async Task<ApprovalStatsDto> GetApprovalStatsAsync(
        Guid userId,
        CancellationToken cancellationToken)
    {
        var now = DateTime.UtcNow;
        var startOfMonth = new DateTime(now.Year, now.Month, 1, 0, 0, 0, DateTimeKind.Utc);

        // Get all approval levels for this user
        var userLevels = await _context.ApprovalLevels
            .Where(al => al.ApproverUserId == userId)
            .ToListAsync(cancellationToken);

        // Count pending
        var pendingCount = userLevels.Count(al =>
            al.Status == ApprovalLevelStatus.Active);

        // Count by decision type
        var approvedCount = userLevels.Count(al =>
            al.Decision == ApprovalDecision.Approve);

        var rejectedCount = userLevels.Count(al =>
            al.Decision == ApprovalDecision.Reject);

        var returnedCount = userLevels.Count(al =>
            al.Decision == ApprovalDecision.ReturnForRevision);

        // Count this month
        var totalThisMonth = userLevels.Count(al =>
            al.DecidedAt.HasValue && al.DecidedAt >= startOfMonth);

        // Calculate average response time (from NotifiedAt to DecidedAt)
        var completedLevels = userLevels
            .Where(al => al.NotifiedAt.HasValue && al.DecidedAt.HasValue)
            .ToList();

        decimal? averageResponseTimeHours = null;
        if (completedLevels.Any())
        {
            var totalHours = completedLevels
                .Sum(al => (al.DecidedAt!.Value - al.NotifiedAt!.Value).TotalHours);
            averageResponseTimeHours = (decimal)(totalHours / completedLevels.Count);
        }

        return new ApprovalStatsDto
        {
            PendingCount = pendingCount,
            ApprovedCount = approvedCount,
            RejectedCount = rejectedCount,
            ReturnedCount = returnedCount,
            TotalThisMonth = totalThisMonth,
            AverageResponseTimeHours = averageResponseTimeHours
        };
    }
}
