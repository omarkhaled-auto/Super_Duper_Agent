using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Approval.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Approval.Queries.GetPendingApprovals;

/// <summary>
/// Handler for GetPendingApprovalsQuery.
/// </summary>
public class GetPendingApprovalsQueryHandler : IRequestHandler<GetPendingApprovalsQuery, PaginatedList<PendingApprovalDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public GetPendingApprovalsQueryHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<PaginatedList<PendingApprovalDto>> Handle(GetPendingApprovalsQuery request, CancellationToken cancellationToken)
    {
        var userId = request.UserId ?? _currentUserService.UserId
            ?? throw new UnauthorizedAccessException("User must be authenticated to view pending approvals.");

        // Query for active approval levels where the user is the approver
        var query = _context.ApprovalLevels
            .Include(l => l.Workflow)
                .ThenInclude(w => w.Tender)
                    .ThenInclude(t => t.Client)
            .Include(l => l.Workflow)
                .ThenInclude(w => w.Initiator)
            .Where(l => l.ApproverUserId == userId)
            .Where(l => l.Status == ApprovalLevelStatus.Active)
            .Where(l => l.Workflow.Status == ApprovalWorkflowStatus.InProgress)
            .AsNoTracking();

        // Apply search filter
        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchTerm = request.Search.ToLower();
            query = query.Where(l =>
                l.Workflow.Tender.Reference.ToLower().Contains(searchTerm) ||
                l.Workflow.Tender.Title.ToLower().Contains(searchTerm));
        }

        // Apply overdue filter
        if (request.OverdueOnly == true)
        {
            var now = DateTime.UtcNow;
            query = query.Where(l => l.Deadline.HasValue && l.Deadline.Value < now);
        }

        // Order by notified date (oldest first, so they're actioned in order)
        query = query.OrderBy(l => l.NotifiedAt ?? l.CreatedAt);

        // Get total count
        var totalCount = await query.CountAsync(cancellationToken);

        // Apply pagination
        var items = await query
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .ToListAsync(cancellationToken);

        // Get total levels count for each workflow
        var workflowIds = items.Select(l => l.WorkflowId).Distinct().ToList();
        var levelCounts = await _context.ApprovalLevels
            .Where(l => workflowIds.Contains(l.WorkflowId))
            .GroupBy(l => l.WorkflowId)
            .Select(g => new { WorkflowId = g.Key, Count = g.Count() })
            .ToDictionaryAsync(x => x.WorkflowId, x => x.Count, cancellationToken);

        // Map to DTOs
        var dtos = items.Select(l => new PendingApprovalDto
        {
            WorkflowId = l.WorkflowId,
            TenderId = l.Workflow.TenderId,
            TenderReference = l.Workflow.Tender.Reference,
            TenderTitle = l.Workflow.Tender.Title,
            ClientName = l.Workflow.Tender.Client.Name,
            LevelNumber = l.LevelNumber,
            TotalLevels = levelCounts.GetValueOrDefault(l.WorkflowId, 3),
            InitiatedByName = l.Workflow.Initiator.FullName,
            InitiatedAt = l.Workflow.InitiatedAt,
            NotifiedAt = l.NotifiedAt,
            Deadline = l.Deadline,
            WorkflowStatus = l.Workflow.Status
        }).ToList();

        return new PaginatedList<PendingApprovalDto>(dtos, totalCount, request.Page, request.PageSize);
    }
}
