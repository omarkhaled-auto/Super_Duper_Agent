using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.TechnicalEvaluation.Commands.LockTechnicalScores;

/// <summary>
/// Handler for LockTechnicalScoresCommand.
/// </summary>
public class LockTechnicalScoresCommandHandler
    : IRequestHandler<LockTechnicalScoresCommand, LockTechnicalScoresResult>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<LockTechnicalScoresCommandHandler> _logger;

    public LockTechnicalScoresCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService,
        ILogger<LockTechnicalScoresCommandHandler> logger)
    {
        _context = context;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<LockTechnicalScoresResult> Handle(
        LockTechnicalScoresCommand request,
        CancellationToken cancellationToken)
    {
        // Verify confirmation flag
        if (!request.Confirm)
        {
            return new LockTechnicalScoresResult
            {
                TenderId = request.TenderId,
                Success = false,
                ErrorMessage = "Confirmation required. Set Confirm to true to proceed with locking scores. This action is irreversible."
            };
        }

        var currentUserId = _currentUserService.UserId;
        if (currentUserId == null)
        {
            return new LockTechnicalScoresResult
            {
                TenderId = request.TenderId,
                Success = false,
                ErrorMessage = "Current user not found."
            };
        }

        // Get evaluation state
        var evaluationState = await _context.EvaluationStates
            .FirstOrDefaultAsync(e => e.TenderId == request.TenderId, cancellationToken);

        if (evaluationState == null)
        {
            return new LockTechnicalScoresResult
            {
                TenderId = request.TenderId,
                Success = false,
                ErrorMessage = "Evaluation setup not found for this tender."
            };
        }

        // Check if already locked
        if (evaluationState.TechnicalScoresLocked)
        {
            return new LockTechnicalScoresResult
            {
                TenderId = request.TenderId,
                LockedAt = evaluationState.TechnicalLockedAt,
                Success = false,
                ErrorMessage = "Technical scores are already locked."
            };
        }

        // Get panelist completion stats
        var panelists = await _context.EvaluationPanels
            .Where(p => p.TenderId == request.TenderId)
            .ToListAsync(cancellationToken);

        var incompletePanelistCount = panelists.Count(p => p.CompletedAt == null);

        // Get bidder scoring stats
        var bidderIds = await _context.BidSubmissions
            .Where(b => b.TenderId == request.TenderId)
            .Select(b => b.BidderId)
            .ToListAsync(cancellationToken);

        var criteriaCount = await _context.EvaluationCriteria
            .CountAsync(c => c.TenderId == request.TenderId, cancellationToken);

        var panelistCount = panelists.Count;
        var expectedScoresPerBidder = criteriaCount * panelistCount;

        var incompleteBidderCount = 0;
        foreach (var bidderId in bidderIds)
        {
            var scoreCount = await _context.TechnicalScores
                .CountAsync(s => s.TenderId == request.TenderId &&
                               s.BidderId == bidderId &&
                               !s.IsDraft,
                           cancellationToken);

            if (scoreCount < expectedScoresPerBidder)
            {
                incompleteBidderCount++;
            }
        }

        // Lock the scores
        var now = DateTime.UtcNow;
        evaluationState.TechnicalScoresLocked = true;
        evaluationState.TechnicalLockedAt = now;
        evaluationState.TechnicalLockedBy = currentUserId.Value;

        // Also finalize any remaining draft scores
        var draftScores = await _context.TechnicalScores
            .Where(s => s.TenderId == request.TenderId && s.IsDraft)
            .ToListAsync(cancellationToken);

        foreach (var score in draftScores)
        {
            score.IsDraft = false;
            score.SubmittedAt = now;
        }

        await _context.SaveChangesAsync(cancellationToken);

        // Get user name for response
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == currentUserId.Value, cancellationToken);

        _logger.LogInformation(
            "Technical scores locked for tender {TenderId} by user {UserId}. " +
            "Incomplete panelists: {IncompletePanelists}, Incomplete bidders: {IncompleteBidders}",
            request.TenderId, currentUserId, incompletePanelistCount, incompleteBidderCount);

        return new LockTechnicalScoresResult
        {
            TenderId = request.TenderId,
            LockedAt = now,
            LockedByName = user?.FullName,
            Success = true,
            IncompletePanelistCount = incompletePanelistCount,
            IncompleteBidderCount = incompleteBidderCount
        };
    }
}
