using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Dashboard.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Dashboard.Queries.GetTenderManagerDashboard;

/// <summary>
/// Handler for the GetTenderManagerDashboardQuery.
/// </summary>
public class GetTenderManagerDashboardQueryHandler
    : IRequestHandler<GetTenderManagerDashboardQuery, TenderManagerDashboardDto>
{
    private readonly IApplicationDbContext _context;

    public GetTenderManagerDashboardQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<TenderManagerDashboardDto> Handle(
        GetTenderManagerDashboardQuery request,
        CancellationToken cancellationToken)
    {
        var now = DateTime.UtcNow;
        var startOfMonth = new DateTime(now.Year, now.Month, 1, 0, 0, 0, DateTimeKind.Utc);
        var deadlineCutoff = now.AddDays(request.DeadlineDaysAhead);

        // Get KPIs
        var kpis = await GetKpisAsync(startOfMonth, cancellationToken);

        // Get recent active tenders
        var activeTenders = await GetActiveTendersAsync(request.ActiveTendersLimit, cancellationToken);

        // Get upcoming deadlines
        var upcomingDeadlines = await GetUpcomingDeadlinesAsync(now, deadlineCutoff, cancellationToken);

        // Get recent activity
        var recentActivity = await GetRecentActivityAsync(request.ActivityLimit, cancellationToken);

        return new TenderManagerDashboardDto
        {
            Kpis = kpis,
            ActiveTenders = activeTenders,
            UpcomingDeadlines = upcomingDeadlines,
            RecentActivity = recentActivity
        };
    }

    private async Task<List<DashboardKpiDto>> GetKpisAsync(
        DateTime startOfMonth,
        CancellationToken cancellationToken)
    {
        var kpis = new List<DashboardKpiDto>();

        // Active Tenders count
        var activeTendersCount = await _context.Tenders
            .CountAsync(t => t.Status == TenderStatus.Active, cancellationToken);

        kpis.Add(new DashboardKpiDto
        {
            Name = "Active Tenders",
            Value = activeTendersCount,
            Icon = "pi-file",
            Color = "blue"
        });

        // In Evaluation count
        var inEvaluationCount = await _context.Tenders
            .CountAsync(t => t.Status == TenderStatus.Evaluation, cancellationToken);

        kpis.Add(new DashboardKpiDto
        {
            Name = "In Evaluation",
            Value = inEvaluationCount,
            Icon = "pi-chart-bar",
            Color = "orange"
        });

        // Awarded This Month
        var awardedThisMonth = await _context.Tenders
            .CountAsync(t => t.Status == TenderStatus.Awarded &&
                           t.UpdatedAt >= startOfMonth, cancellationToken);

        kpis.Add(new DashboardKpiDto
        {
            Name = "Awarded This Month",
            Value = awardedThisMonth,
            Icon = "pi-trophy",
            Color = "green"
        });

        // Overdue Tasks (tenders past submission deadline but still active)
        var now = DateTime.UtcNow;
        var overdueCount = await _context.Tenders
            .CountAsync(t => t.Status == TenderStatus.Active &&
                           t.SubmissionDeadline < now, cancellationToken);

        kpis.Add(new DashboardKpiDto
        {
            Name = "Overdue Tasks",
            Value = overdueCount,
            Icon = "pi-exclamation-triangle",
            Color = "red"
        });

        return kpis;
    }

    private async Task<List<ActiveTenderDto>> GetActiveTendersAsync(
        int limit,
        CancellationToken cancellationToken)
    {
        return await _context.Tenders
            .Include(t => t.Client)
            .Include(t => t.TenderBidders)
            .Include(t => t.BidSubmissions)
            .Where(t => t.Status == TenderStatus.Active || t.Status == TenderStatus.Evaluation)
            .OrderByDescending(t => t.CreatedAt)
            .Take(limit)
            .Select(t => new ActiveTenderDto
            {
                Id = t.Id,
                Reference = t.Reference,
                Title = t.Title,
                ClientName = t.Client.Name,
                Status = t.Status,
                SubmissionDeadline = t.SubmissionDeadline,
                BidsReceived = t.BidSubmissions.Count,
                InvitedBidders = t.TenderBidders.Count,
                CreatedAt = t.CreatedAt
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);
    }

    private async Task<List<DeadlineItemDto>> GetUpcomingDeadlinesAsync(
        DateTime now,
        DateTime cutoff,
        CancellationToken cancellationToken)
    {
        var deadlines = new List<DeadlineItemDto>();

        // Get tenders with upcoming submission deadlines
        var submissionDeadlines = await _context.Tenders
            .Where(t => t.Status == TenderStatus.Active &&
                       t.SubmissionDeadline >= now &&
                       t.SubmissionDeadline <= cutoff)
            .OrderBy(t => t.SubmissionDeadline)
            .Select(t => new DeadlineItemDto
            {
                TenderId = t.Id,
                TenderReference = t.Reference,
                TenderTitle = t.Title,
                DeadlineType = "Submission",
                Deadline = t.SubmissionDeadline
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        deadlines.AddRange(submissionDeadlines);

        // Get tenders with upcoming clarification deadlines
        var clarificationDeadlines = await _context.Tenders
            .Where(t => t.Status == TenderStatus.Active &&
                       t.ClarificationDeadline >= now &&
                       t.ClarificationDeadline <= cutoff)
            .OrderBy(t => t.ClarificationDeadline)
            .Select(t => new DeadlineItemDto
            {
                TenderId = t.Id,
                TenderReference = t.Reference,
                TenderTitle = t.Title,
                DeadlineType = "Clarification",
                Deadline = t.ClarificationDeadline
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        deadlines.AddRange(clarificationDeadlines);

        // Sort all deadlines by date
        return deadlines.OrderBy(d => d.Deadline).ToList();
    }

    private async Task<List<ActivityFeedItemDto>> GetRecentActivityAsync(
        int limit,
        CancellationToken cancellationToken)
    {
        // Get recent audit log entries related to tenders
        return await _context.AuditLogs
            .Where(a => a.EntityType == "Tender" ||
                       a.EntityType == "BidSubmission" ||
                       a.EntityType == "ApprovalWorkflow")
            .OrderByDescending(a => a.CreatedAt)
            .Take(limit)
            .Select(a => new ActivityFeedItemDto
            {
                Id = a.Id,
                ActivityType = a.Action,
                Description = $"{a.Action} on {a.EntityType}",
                EntityType = a.EntityType,
                EntityId = a.EntityId,
                PerformedBy = a.UserEmail,
                OccurredAt = a.CreatedAt,
                Icon = GetActivityIcon(a.Action),
                Color = GetActivityColor(a.Action)
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);
    }

    private static string GetActivityIcon(string activityType)
    {
        return activityType.ToLower() switch
        {
            "created" or "create" => "pi-plus-circle",
            "updated" or "update" => "pi-pencil",
            "deleted" or "delete" => "pi-trash",
            "published" or "publish" => "pi-send",
            "submitted" or "submit" => "pi-upload",
            "approved" or "approve" => "pi-check-circle",
            "rejected" or "reject" => "pi-times-circle",
            "awarded" or "award" => "pi-trophy",
            _ => "pi-info-circle"
        };
    }

    private static string GetActivityColor(string activityType)
    {
        return activityType.ToLower() switch
        {
            "created" or "create" => "blue",
            "updated" or "update" => "orange",
            "deleted" or "delete" => "red",
            "published" or "publish" => "green",
            "submitted" or "submit" => "purple",
            "approved" or "approve" => "green",
            "rejected" or "reject" => "red",
            "awarded" or "award" => "gold",
            _ => "gray"
        };
    }
}
