using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Dashboard.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Dashboard.Queries.GetOverviewDashboard;

/// <summary>
/// Handler for the GetOverviewDashboardQuery.
/// </summary>
public class GetOverviewDashboardQueryHandler
    : IRequestHandler<GetOverviewDashboardQuery, OverviewDashboardDto>
{
    private readonly IApplicationDbContext _context;

    public GetOverviewDashboardQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<OverviewDashboardDto> Handle(
        GetOverviewDashboardQuery request,
        CancellationToken cancellationToken)
    {
        var now = DateTime.UtcNow;

        // Get tender counts by status
        var tenderCounts = await GetTenderCountsByStatusAsync(cancellationToken);

        // Get bidder counts
        var totalBidders = await _context.Bidders
            .CountAsync(cancellationToken);

        var activeBidders = await _context.Bidders
            .CountAsync(b => b.IsActive, cancellationToken);

        // Get pending approvals count
        var pendingApprovals = await _context.ApprovalWorkflows
            .CountAsync(w => w.Status == ApprovalWorkflowStatus.InProgress, cancellationToken);

        // Get total contract value from awarded tenders' winning bid submissions
        var totalContractValue = await _context.BidSubmissions
            .Where(bs => bs.Tender.Status == TenderStatus.Awarded)
            .SumAsync(bs => bs.NormalizedTotalAmount ?? 0m, cancellationToken);

        // Get monthly trend data
        var monthlyTrend = await GetMonthlyTrendAsync(now, request.MonthsBack, cancellationToken);

        return new OverviewDashboardDto
        {
            TenderCounts = tenderCounts,
            TotalBidders = totalBidders,
            ActiveBidders = activeBidders,
            PendingApprovals = pendingApprovals,
            TotalContractValue = totalContractValue,
            Currency = "SAR",
            MonthlyTrend = monthlyTrend
        };
    }

    private async Task<TenderCountsByStatusDto> GetTenderCountsByStatusAsync(
        CancellationToken cancellationToken)
    {
        var statusCounts = await _context.Tenders
            .GroupBy(t => t.Status)
            .Select(g => new { Status = g.Key, Count = g.Count() })
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        var counts = new TenderCountsByStatusDto
        {
            Draft = statusCounts.FirstOrDefault(s => s.Status == TenderStatus.Draft)?.Count ?? 0,
            Active = statusCounts.FirstOrDefault(s => s.Status == TenderStatus.Active)?.Count ?? 0,
            Evaluation = statusCounts.FirstOrDefault(s => s.Status == TenderStatus.Evaluation)?.Count ?? 0,
            Awarded = statusCounts.FirstOrDefault(s => s.Status == TenderStatus.Awarded)?.Count ?? 0,
            Cancelled = statusCounts.FirstOrDefault(s => s.Status == TenderStatus.Cancelled)?.Count ?? 0
        };

        counts.Total = counts.Draft + counts.Active + counts.Evaluation + counts.Awarded + counts.Cancelled;

        return counts;
    }

    private async Task<List<MonthlyTrendItemDto>> GetMonthlyTrendAsync(
        DateTime now,
        int monthsBack,
        CancellationToken cancellationToken)
    {
        var cutoffDate = new DateTime(now.Year, now.Month, 1, 0, 0, 0, DateTimeKind.Utc)
            .AddMonths(-monthsBack + 1);

        // Get tenders created per month
        var tendersPerMonth = await _context.Tenders
            .Where(t => t.CreatedAt >= cutoffDate)
            .GroupBy(t => new { t.CreatedAt.Year, t.CreatedAt.Month })
            .Select(g => new
            {
                g.Key.Year,
                g.Key.Month,
                Count = g.Count()
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Get bids received per month
        var bidsPerMonth = await _context.BidSubmissions
            .Where(bs => bs.SubmissionTime >= cutoffDate)
            .GroupBy(bs => new { bs.SubmissionTime.Year, bs.SubmissionTime.Month })
            .Select(g => new
            {
                g.Key.Year,
                g.Key.Month,
                Count = g.Count()
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Get contract value of tenders awarded per month
        var contractValuePerMonth = await _context.Tenders
            .Where(t => t.Status == TenderStatus.Awarded &&
                        t.AwardedAt != null &&
                        t.AwardedAt >= cutoffDate)
            .GroupBy(t => new { t.AwardedAt!.Value.Year, t.AwardedAt!.Value.Month })
            .Select(g => new
            {
                g.Key.Year,
                g.Key.Month,
                Value = g.SelectMany(t => t.BidSubmissions)
                    .Sum(bs => bs.NormalizedTotalAmount ?? 0m)
            })
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Build the trend list for each month in the range
        var result = new List<MonthlyTrendItemDto>();
        for (var i = 0; i < monthsBack; i++)
        {
            var monthDate = cutoffDate.AddMonths(i);
            var year = monthDate.Year;
            var month = monthDate.Month;

            result.Add(new MonthlyTrendItemDto
            {
                Month = $"{year:D4}-{month:D2}",
                TendersCreated = tendersPerMonth
                    .FirstOrDefault(t => t.Year == year && t.Month == month)?.Count ?? 0,
                BidsReceived = bidsPerMonth
                    .FirstOrDefault(b => b.Year == year && b.Month == month)?.Count ?? 0,
                ContractValue = contractValuePerMonth
                    .FirstOrDefault(c => c.Year == year && c.Month == month)?.Value ?? 0m
            });
        }

        return result;
    }
}
