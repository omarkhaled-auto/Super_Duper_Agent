using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetEvaluationSetup;

/// <summary>
/// Handler for GetEvaluationSetupQuery.
/// </summary>
public class GetEvaluationSetupQueryHandler : IRequestHandler<GetEvaluationSetupQuery, EvaluationSetupDto?>
{
    private readonly IApplicationDbContext _context;

    public GetEvaluationSetupQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<EvaluationSetupDto?> Handle(
        GetEvaluationSetupQuery request,
        CancellationToken cancellationToken)
    {
        // Get tender with related data
        var tender = await _context.Tenders
            .Include(t => t.EvaluationState)
                .ThenInclude(e => e!.LockedByUser)
            .Include(t => t.EvaluationPanels)
                .ThenInclude(p => p.Panelist)
            .Include(t => t.EvaluationCriteria.OrderBy(c => c.SortOrder))
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            return null;
        }

        // Get bidder count
        var bidderCount = await _context.BidSubmissions
            .CountAsync(b => b.TenderId == request.TenderId, cancellationToken);

        // Calculate panelist progress
        var criteriaCount = tender.EvaluationCriteria.Count;
        var panelistDtos = new List<PanelistDto>();

        foreach (var panel in tender.EvaluationPanels)
        {
            // Count unique bidders scored by this panelist
            var biddersScored = await _context.TechnicalScores
                .Where(s => s.TenderId == request.TenderId &&
                           s.PanelistUserId == panel.PanelistUserId &&
                           !s.IsDraft)
                .Select(s => s.BidderId)
                .Distinct()
                .CountAsync(cancellationToken);

            // A bidder is considered "fully scored" when all criteria have scores
            var bidderWithFullScoresCount = 0;
            var bidderIds = await _context.BidSubmissions
                .Where(b => b.TenderId == request.TenderId)
                .Select(b => b.BidderId)
                .ToListAsync(cancellationToken);

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

        var isSetupComplete = tender.EvaluationState != null &&
                              tender.EvaluationPanels.Any() &&
                              tender.EvaluationCriteria.Any();

        return new EvaluationSetupDto
        {
            TenderId = tender.Id,
            TenderTitle = tender.Title,
            TenderReference = tender.Reference,
            ScoringMethod = tender.EvaluationState?.ScoringMethod ?? Domain.Enums.ScoringMethod.Numeric,
            BlindMode = tender.EvaluationState?.BlindMode ?? true,
            TechnicalEvaluationDeadline = tender.EvaluationState?.TechnicalEvaluationDeadline,
            TechnicalScoresLocked = tender.EvaluationState?.TechnicalScoresLocked ?? false,
            TechnicalLockedAt = tender.EvaluationState?.TechnicalLockedAt,
            TechnicalLockedByName = tender.EvaluationState?.LockedByUser?.FullName,
            TechnicalWeight = tender.TechnicalWeight,
            CommercialWeight = tender.CommercialWeight,
            Panelists = panelistDtos,
            Criteria = tender.EvaluationCriteria.Select(c => new EvaluationCriterionInfoDto
            {
                Id = c.Id,
                Name = c.Name,
                WeightPercentage = c.WeightPercentage,
                GuidanceNotes = c.GuidanceNotes,
                SortOrder = c.SortOrder
            }).ToList(),
            BidderCount = bidderCount,
            IsSetupComplete = isSetupComplete
        };
    }
}
