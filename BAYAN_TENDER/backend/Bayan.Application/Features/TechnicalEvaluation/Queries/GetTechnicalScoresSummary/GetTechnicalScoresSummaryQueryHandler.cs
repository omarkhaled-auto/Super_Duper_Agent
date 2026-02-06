using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetTechnicalScoresSummary;

/// <summary>
/// Handler for GetTechnicalScoresSummaryQuery.
/// </summary>
public class GetTechnicalScoresSummaryQueryHandler
    : IRequestHandler<GetTechnicalScoresSummaryQuery, TechnicalScoresSummaryDto?>
{
    private readonly IApplicationDbContext _context;

    public GetTechnicalScoresSummaryQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<TechnicalScoresSummaryDto?> Handle(
        GetTechnicalScoresSummaryQuery request,
        CancellationToken cancellationToken)
    {
        // Get tender
        var tender = await _context.Tenders
            .Include(t => t.EvaluationState)
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            return null;
        }

        // Get criteria
        var criteria = await _context.EvaluationCriteria
            .Where(c => c.TenderId == request.TenderId)
            .OrderBy(c => c.SortOrder)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Get panelists
        var panels = await _context.EvaluationPanels
            .Include(p => p.Panelist)
            .Where(p => p.TenderId == request.TenderId)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Get all scores
        var allScores = await _context.TechnicalScores
            .Include(s => s.Panelist)
            .Include(s => s.Criterion)
            .Include(s => s.Bidder)
            .Where(s => s.TenderId == request.TenderId)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Get bidders
        var bidders = await _context.BidSubmissions
            .Include(b => b.Bidder)
            .Where(b => b.TenderId == request.TenderId)
            .OrderBy(b => b.BidderId)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        var criteriaCount = criteria.Count;
        var panelistCount = panels.Count;
        var expectedScoresPerBidder = criteriaCount * panelistCount;

        // Build bidder scores summary
        var bidderScores = new List<BidderScoresSummaryDto>();
        var bidderIndex = 1;

        foreach (var submission in bidders)
        {
            var bidderAllScores = allScores.Where(s => s.BidderId == submission.BidderId).ToList();
            var anonymousId = $"Bidder {bidderIndex:D3}";

            // Scores grouped by criterion
            var criterionScores = new List<CriterionScoreAverageDto>();

            foreach (var criterion in criteria)
            {
                var scoresForCriterion = bidderAllScores
                    .Where(s => s.CriterionId == criterion.Id && !s.IsDraft)
                    .Select(s => s.Score)
                    .ToList();

                if (scoresForCriterion.Any())
                {
                    var avgScore = scoresForCriterion.Average();
                    var minScore = scoresForCriterion.Min();
                    var maxScore = scoresForCriterion.Max();

                    // Calculate variance
                    var variance = scoresForCriterion.Count > 1
                        ? scoresForCriterion.Select(s => Math.Pow((double)(s - (decimal)avgScore), 2)).Average()
                        : 0;

                    criterionScores.Add(new CriterionScoreAverageDto
                    {
                        CriterionId = criterion.Id,
                        CriterionName = criterion.Name,
                        WeightPercentage = criterion.WeightPercentage,
                        AverageScore = Math.Round((decimal)avgScore, 2),
                        WeightedAverageScore = Math.Round((decimal)avgScore * criterion.WeightPercentage / 100, 2),
                        MinScore = minScore,
                        MaxScore = maxScore,
                        Variance = Math.Round((decimal)variance, 4)
                    });
                }
                else
                {
                    criterionScores.Add(new CriterionScoreAverageDto
                    {
                        CriterionId = criterion.Id,
                        CriterionName = criterion.Name,
                        WeightPercentage = criterion.WeightPercentage,
                        AverageScore = 0,
                        WeightedAverageScore = 0,
                        MinScore = 0,
                        MaxScore = 0,
                        Variance = 0
                    });
                }
            }

            // Detailed panelist scores
            var panelistScores = bidderAllScores.Select(s => new PanelistCriterionScoreDto
            {
                PanelistUserId = s.PanelistUserId,
                PanelistName = s.Panelist.FullName,
                CriterionId = s.CriterionId,
                CriterionName = s.Criterion.Name,
                Score = s.Score,
                Comment = s.Comment,
                IsDraft = s.IsDraft,
                SubmittedAt = s.SubmittedAt
            }).ToList();

            // Calculate total weighted score
            var totalWeightedScore = criterionScores.Sum(c => c.WeightedAverageScore);

            // Calculate overall variance across panelists
            var panelistTotals = panels.Select(p =>
            {
                var pScores = bidderAllScores.Where(s => s.PanelistUserId == p.PanelistUserId && !s.IsDraft);
                return pScores.Sum(s => s.Score * s.Criterion.WeightPercentage / 100);
            }).ToList();

            var scoreVariance = 0m;
            var standardDeviation = 0m;

            if (panelistTotals.Count > 1 && panelistTotals.Any(t => t > 0))
            {
                var avgTotal = panelistTotals.Average();
                scoreVariance = (decimal)panelistTotals.Select(t => Math.Pow((double)(t - avgTotal), 2)).Average();
                standardDeviation = (decimal)Math.Sqrt((double)scoreVariance);
            }

            var finalizedScoreCount = bidderAllScores.Count(s => !s.IsDraft);
            var isFullyScored = finalizedScoreCount >= expectedScoresPerBidder;

            bidderScores.Add(new BidderScoresSummaryDto
            {
                BidderId = submission.BidderId,
                CompanyName = submission.Bidder.CompanyName,
                AnonymousId = anonymousId,
                CriterionScores = criterionScores,
                PanelistScores = panelistScores,
                TotalWeightedScore = Math.Round(totalWeightedScore, 2),
                ScoreVariance = Math.Round(scoreVariance, 4),
                StandardDeviation = Math.Round(standardDeviation, 4),
                PanelistsScored = bidderAllScores.Where(s => !s.IsDraft).Select(s => s.PanelistUserId).Distinct().Count(),
                IsFullyScored = isFullyScored
            });

            bidderIndex++;
        }

        // Calculate ranks
        var rankedBidders = bidderScores.OrderByDescending(b => b.TotalWeightedScore).ToList();
        for (int i = 0; i < rankedBidders.Count; i++)
        {
            rankedBidders[i].Rank = i + 1;
        }

        // Panelist completion status
        var completedPanelistCount = panels.Count(p => p.CompletedAt != null);

        return new TechnicalScoresSummaryDto
        {
            TenderId = tender.Id,
            TenderTitle = tender.Title,
            TechnicalScoresLocked = tender.EvaluationState?.TechnicalScoresLocked ?? false,
            LockedAt = tender.EvaluationState?.TechnicalLockedAt,
            Criteria = criteria.Select(c => new CriteriaSummaryDto
            {
                Id = c.Id,
                Name = c.Name,
                WeightPercentage = c.WeightPercentage,
                SortOrder = c.SortOrder
            }).ToList(),
            Panelists = panels.Select(p => new PanelistSummaryDto
            {
                UserId = p.PanelistUserId,
                FullName = p.Panelist.FullName,
                HasCompletedScoring = p.CompletedAt != null
            }).ToList(),
            BidderScores = bidderScores,
            CompletedPanelistCount = completedPanelistCount,
            TotalPanelistCount = panels.Count
        };
    }
}
