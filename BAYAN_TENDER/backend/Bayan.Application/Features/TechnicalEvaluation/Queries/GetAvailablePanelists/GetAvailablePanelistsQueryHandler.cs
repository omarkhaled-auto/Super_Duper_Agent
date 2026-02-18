using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetAvailablePanelists;

/// <summary>
/// Handler for GetAvailablePanelistsQuery.
/// Returns active internal users (non-Bidder) who are not already assigned to this tender.
/// </summary>
public class GetAvailablePanelistsQueryHandler : IRequestHandler<GetAvailablePanelistsQuery, List<PanelistDto>>
{
    private readonly IApplicationDbContext _context;

    public GetAvailablePanelistsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<PanelistDto>> Handle(
        GetAvailablePanelistsQuery request,
        CancellationToken cancellationToken)
    {
        // Get IDs of users already assigned as panelists for this tender
        var assignedUserIds = await _context.EvaluationPanels
            .Where(p => p.TenderId == request.TenderId)
            .Select(p => p.PanelistUserId)
            .ToListAsync(cancellationToken);

        // Get all active internal users (exclude Bidder role and already-assigned)
        var availableUsers = await _context.Users
            .Where(u => u.IsActive &&
                        u.Role != UserRole.Bidder &&
                        !assignedUserIds.Contains(u.Id))
            .OrderBy(u => u.FirstName)
            .ThenBy(u => u.LastName)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        return availableUsers.Select(u => new PanelistDto
        {
            Id = u.Id,
            UserId = u.Id,
            FullName = u.FullName,
            Email = u.Email,
            Department = u.Department,
            JobTitle = u.JobTitle,
            AssignedAt = default,
            CompletedAt = null,
            BiddersScored = 0,
            TotalBidders = 0
        }).ToList();
    }
}
