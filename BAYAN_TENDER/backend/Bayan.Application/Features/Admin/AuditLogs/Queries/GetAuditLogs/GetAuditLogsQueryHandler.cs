namespace Bayan.Application.Features.Admin.AuditLogs.Queries.GetAuditLogs;

using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Admin.AuditLogs.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

/// <summary>
/// Handler for retrieving paginated and filtered audit logs.
/// </summary>
public class GetAuditLogsQueryHandler : IRequestHandler<GetAuditLogsQuery, PaginatedList<AuditLogDto>>
{
    private readonly IApplicationDbContext _context;

    public GetAuditLogsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<PaginatedList<AuditLogDto>> Handle(GetAuditLogsQuery request, CancellationToken cancellationToken)
    {
        var query = _context.AuditLogs
            .Include(a => a.User)
            .AsQueryable();

        // Apply filters
        if (request.UserId.HasValue)
        {
            query = query.Where(a => a.UserId == request.UserId.Value);
        }

        if (!string.IsNullOrWhiteSpace(request.Action))
        {
            query = query.Where(a => a.Action.Contains(request.Action));
        }

        if (!string.IsNullOrWhiteSpace(request.EntityType))
        {
            query = query.Where(a => a.EntityType == request.EntityType);
        }

        if (request.EntityId.HasValue)
        {
            query = query.Where(a => a.EntityId == request.EntityId.Value);
        }

        if (request.StartDate.HasValue)
        {
            var startDate = request.StartDate.Value.Date;
            query = query.Where(a => a.CreatedAt >= startDate);
        }

        if (request.EndDate.HasValue)
        {
            var endDate = request.EndDate.Value.Date.AddDays(1);
            query = query.Where(a => a.CreatedAt < endDate);
        }

        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchLower = request.Search.ToLower();
            query = query.Where(a =>
                (a.UserEmail != null && a.UserEmail.ToLower().Contains(searchLower)) ||
                a.Action.ToLower().Contains(searchLower) ||
                a.EntityType.ToLower().Contains(searchLower));
        }

        // Order by most recent first
        query = query.OrderByDescending(a => a.CreatedAt);

        // Get total count
        var totalCount = await query.CountAsync(cancellationToken);

        // Apply pagination
        var items = await query
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(a => new AuditLogDto
            {
                Id = a.Id,
                Timestamp = a.CreatedAt,
                UserId = a.UserId,
                UserEmail = a.UserEmail,
                UserFullName = a.User != null ? $"{a.User.FirstName} {a.User.LastName}" : null,
                Action = a.Action,
                EntityType = a.EntityType,
                EntityId = a.EntityId,
                OldValues = a.OldValues,
                NewValues = a.NewValues,
                IpAddress = a.IpAddress,
                UserAgent = a.UserAgent
            })
            .ToListAsync(cancellationToken);

        return new PaginatedList<AuditLogDto>(items, totalCount, request.Page, request.PageSize);
    }
}
