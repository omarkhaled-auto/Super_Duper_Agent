using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelistScores;

/// <summary>
/// Handler for GetPanelistScoresQuery.
/// </summary>
public class GetPanelistScoresQueryHandler : IRequestHandler<GetPanelistScoresQuery, List<TechnicalScoreDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public GetPanelistScoresQueryHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<List<TechnicalScoreDto>> Handle(
        GetPanelistScoresQuery request,
        CancellationToken cancellationToken)
    {
        var currentUserId = _currentUserService.UserId;
        if (currentUserId == null)
        {
            return new List<TechnicalScoreDto>();
        }

        // Verify user is a panelist for this tender
        var isPanelist = await _context.EvaluationPanels
            .AnyAsync(p => p.TenderId == request.TenderId &&
                         p.PanelistUserId == currentUserId.Value,
                     cancellationToken);

        if (!isPanelist)
        {
            return new List<TechnicalScoreDto>();
        }

        // Get evaluation state to check blind mode
        var evaluationState = await _context.EvaluationStates
            .AsNoTracking()
            .FirstOrDefaultAsync(e => e.TenderId == request.TenderId, cancellationToken);

        var blindMode = evaluationState?.BlindMode ?? true;

        // Get bidder info
        var bidder = await _context.Bidders
            .AsNoTracking()
            .FirstOrDefaultAsync(b => b.Id == request.BidderId, cancellationToken);

        // Generate anonymous ID
        var allBidderIds = await _context.BidSubmissions
            .Where(b => b.TenderId == request.TenderId)
            .OrderBy(b => b.BidderId)
            .Select(b => b.BidderId)
            .ToListAsync(cancellationToken);

        var bidderIndex = allBidderIds.IndexOf(request.BidderId) + 1;
        var anonymousId = $"Bidder {bidderIndex:D3}";

        // Get scores
        var scores = await _context.TechnicalScores
            .Include(s => s.Criterion)
            .Where(s => s.TenderId == request.TenderId &&
                       s.BidderId == request.BidderId &&
                       s.PanelistUserId == currentUserId.Value)
            .OrderBy(s => s.Criterion.SortOrder)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        return scores.Select(s => new TechnicalScoreDto
        {
            Id = s.Id,
            TenderId = s.TenderId,
            BidderId = s.BidderId,
            BidderName = blindMode ? null : bidder?.CompanyName,
            AnonymousId = anonymousId,
            PanelistUserId = s.PanelistUserId,
            CriterionId = s.CriterionId,
            CriterionName = s.Criterion.Name,
            CriterionWeight = s.Criterion.WeightPercentage,
            Score = s.Score,
            Comment = s.Comment,
            IsDraft = s.IsDraft,
            SubmittedAt = s.SubmittedAt
        }).ToList();
    }
}
