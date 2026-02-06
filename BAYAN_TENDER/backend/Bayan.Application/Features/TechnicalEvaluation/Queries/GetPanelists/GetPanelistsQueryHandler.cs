using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelists;

/// <summary>
/// Handler for GetPanelistsQuery.
/// </summary>
public class GetPanelistsQueryHandler : IRequestHandler<GetPanelistsQuery, List<PanelistDto>>
{
    private readonly IApplicationDbContext _context;

    public GetPanelistsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<PanelistDto>> Handle(
        GetPanelistsQuery request,
        CancellationToken cancellationToken)
    {
        // Get panelists for this tender
        var panels = await _context.EvaluationPanels
            .Include(p => p.Panelist)
            .Where(p => p.TenderId == request.TenderId)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        if (!panels.Any())
        {
            return new List<PanelistDto>();
        }

        // Get bidder count and criteria count
        var bidderCount = await _context.BidSubmissions
            .CountAsync(b => b.TenderId == request.TenderId, cancellationToken);

        var criteriaCount = await _context.EvaluationCriteria
            .CountAsync(c => c.TenderId == request.TenderId, cancellationToken);

        var bidderIds = await _context.BidSubmissions
            .Where(b => b.TenderId == request.TenderId)
            .Select(b => b.BidderId)
            .ToListAsync(cancellationToken);

        var panelistDtos = new List<PanelistDto>();

        foreach (var panel in panels)
        {
            // Count bidders with complete scores
            var bidderWithFullScoresCount = 0;

            foreach (var bidderId in bidderIds)
            {
                var scoreCount = await _context.TechnicalScores
                    .CountAsync(s => s.TenderId == request.TenderId &&
                                   s.PanelistUserId == panel.PanelistUserId &&
                                   s.BidderId == bidderId &&
                                   !s.IsDraft,
                               cancellationToken);

                if (scoreCount >= criteriaCount)
                {
                    bidderWithFullScoresCount++;
                }
            }

            panelistDtos.Add(new PanelistDto
            {
                Id = panel.Id,
                UserId = panel.PanelistUserId,
                FullName = panel.Panelist.FullName,
                Email = panel.Panelist.Email,
                Department = panel.Panelist.Department,
                JobTitle = panel.Panelist.JobTitle,
                AssignedAt = panel.AssignedAt,
                CompletedAt = panel.CompletedAt,
                BiddersScored = bidderWithFullScoresCount,
                TotalBidders = bidderCount
            });
        }

        return panelistDtos.OrderBy(p => p.AssignedAt).ToList();
    }
}
