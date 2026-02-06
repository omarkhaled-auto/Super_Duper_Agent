using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelistAssignments;

/// <summary>
/// Handler for GetPanelistAssignmentsQuery.
/// </summary>
public class GetPanelistAssignmentsQueryHandler : IRequestHandler<GetPanelistAssignmentsQuery, PanelistAssignmentDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public GetPanelistAssignmentsQueryHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<PanelistAssignmentDto?> Handle(
        GetPanelistAssignmentsQuery request,
        CancellationToken cancellationToken)
    {
        var currentUserId = _currentUserService.UserId;
        if (currentUserId == null)
        {
            return null;
        }

        // Check if user is a panelist for this tender
        var isPanelist = await _context.EvaluationPanels
            .AnyAsync(p => p.TenderId == request.TenderId &&
                         p.PanelistUserId == currentUserId.Value,
                     cancellationToken);

        if (!isPanelist)
        {
            return null;
        }

        // Get tender with evaluation state
        var tender = await _context.Tenders
            .Include(t => t.EvaluationState)
            .Include(t => t.EvaluationCriteria.OrderBy(c => c.SortOrder))
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            return null;
        }

        var blindMode = tender.EvaluationState?.BlindMode ?? true;

        // Get bidders with submissions
        var bidders = await _context.BidSubmissions
            .Include(b => b.Bidder)
            .Where(b => b.TenderId == request.TenderId)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Get current panelist's scores
        var myScores = await _context.TechnicalScores
            .Include(s => s.Criterion)
            .Where(s => s.TenderId == request.TenderId &&
                       s.PanelistUserId == currentUserId.Value)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        var criteriaCount = tender.EvaluationCriteria.Count;
        var bidderAssignments = new List<BidderAssignmentDto>();
        var biddersCompleted = 0;

        // Create anonymous IDs for blind mode
        var bidderIndex = 1;
        foreach (var submission in bidders.OrderBy(b => b.BidderId))
        {
            var bidderScores = myScores.Where(s => s.BidderId == submission.BidderId).ToList();
            var criteriaScored = bidderScores.Count;
            var isFullySubmitted = bidderScores.All(s => !s.IsDraft) && criteriaScored == criteriaCount;

            if (isFullySubmitted)
            {
                biddersCompleted++;
            }

            var anonymousId = $"Bidder {bidderIndex:D3}";

            bidderAssignments.Add(new BidderAssignmentDto
            {
                BidderId = submission.BidderId,
                CompanyName = blindMode ? null : submission.Bidder.CompanyName,
                AnonymousId = anonymousId,
                CriteriaScored = criteriaScored,
                TotalCriteria = criteriaCount,
                IsFullySubmitted = isFullySubmitted,
                Scores = bidderScores.Select(s => new TechnicalScoreDto
                {
                    Id = s.Id,
                    TenderId = s.TenderId,
                    BidderId = s.BidderId,
                    BidderName = blindMode ? null : submission.Bidder.CompanyName,
                    AnonymousId = anonymousId,
                    PanelistUserId = s.PanelistUserId,
                    CriterionId = s.CriterionId,
                    CriterionName = s.Criterion.Name,
                    CriterionWeight = s.Criterion.WeightPercentage,
                    Score = s.Score,
                    Comment = s.Comment,
                    IsDraft = s.IsDraft,
                    SubmittedAt = s.SubmittedAt
                }).ToList()
            });

            bidderIndex++;
        }

        return new PanelistAssignmentDto
        {
            TenderId = tender.Id,
            TenderTitle = tender.Title,
            TenderReference = tender.Reference,
            BlindMode = blindMode,
            EvaluationDeadline = tender.EvaluationState?.TechnicalEvaluationDeadline,
            TechnicalScoresLocked = tender.EvaluationState?.TechnicalScoresLocked ?? false,
            Bidders = bidderAssignments,
            Criteria = tender.EvaluationCriteria.Select(c => new EvaluationCriterionInfoDto
            {
                Id = c.Id,
                Name = c.Name,
                WeightPercentage = c.WeightPercentage,
                GuidanceNotes = c.GuidanceNotes,
                SortOrder = c.SortOrder
            }).ToList(),
            BiddersCompleted = biddersCompleted,
            TotalBidders = bidders.Count
        };
    }
}
