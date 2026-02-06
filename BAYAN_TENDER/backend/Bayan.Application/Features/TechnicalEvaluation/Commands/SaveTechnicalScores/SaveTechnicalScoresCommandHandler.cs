using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.TechnicalEvaluation.Commands.SaveTechnicalScores;

/// <summary>
/// Handler for SaveTechnicalScoresCommand.
/// </summary>
public class SaveTechnicalScoresCommandHandler
    : IRequestHandler<SaveTechnicalScoresCommand, SaveTechnicalScoresResult>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<SaveTechnicalScoresCommandHandler> _logger;

    public SaveTechnicalScoresCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService,
        ILogger<SaveTechnicalScoresCommandHandler> logger)
    {
        _context = context;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<SaveTechnicalScoresResult> Handle(
        SaveTechnicalScoresCommand request,
        CancellationToken cancellationToken)
    {
        var currentUserId = _currentUserService.UserId;
        if (currentUserId == null)
        {
            return new SaveTechnicalScoresResult
            {
                Success = false,
                ErrorMessage = "Current user not found."
            };
        }

        // Verify tender exists and is not locked
        var evaluationState = await _context.EvaluationStates
            .FirstOrDefaultAsync(e => e.TenderId == request.TenderId, cancellationToken);

        if (evaluationState == null)
        {
            return new SaveTechnicalScoresResult
            {
                Success = false,
                ErrorMessage = "Evaluation setup not found for this tender."
            };
        }

        if (evaluationState.TechnicalScoresLocked)
        {
            return new SaveTechnicalScoresResult
            {
                Success = false,
                ErrorMessage = "Technical scores are locked and cannot be modified."
            };
        }

        // Verify user is a panelist for this tender
        var isPanelist = await _context.EvaluationPanels
            .AnyAsync(p => p.TenderId == request.TenderId &&
                         p.PanelistUserId == currentUserId.Value,
                     cancellationToken);

        if (!isPanelist)
        {
            return new SaveTechnicalScoresResult
            {
                Success = false,
                ErrorMessage = "You are not assigned as a panelist for this tender."
            };
        }

        // Get existing scores for this panelist
        var existingScores = await _context.TechnicalScores
            .Where(s => s.TenderId == request.TenderId &&
                       s.PanelistUserId == currentUserId.Value)
            .ToListAsync(cancellationToken);

        // Get valid bidders and criteria
        var validBidderIds = await _context.BidSubmissions
            .Where(b => b.TenderId == request.TenderId)
            .Select(b => b.BidderId)
            .ToListAsync(cancellationToken);

        var validCriteriaIds = await _context.EvaluationCriteria
            .Where(c => c.TenderId == request.TenderId)
            .Select(c => c.Id)
            .ToListAsync(cancellationToken);

        var validationErrors = new List<ScoreValidationError>();
        var scoresSaved = 0;
        var now = DateTime.UtcNow;

        foreach (var scoreDto in request.Scores)
        {
            // Validate bidder exists
            if (!validBidderIds.Contains(scoreDto.BidderId))
            {
                validationErrors.Add(new ScoreValidationError
                {
                    BidderId = scoreDto.BidderId,
                    CriterionId = scoreDto.CriterionId,
                    ErrorMessage = "Invalid bidder ID."
                });
                continue;
            }

            // Validate criterion exists
            if (!validCriteriaIds.Contains(scoreDto.CriterionId))
            {
                validationErrors.Add(new ScoreValidationError
                {
                    BidderId = scoreDto.BidderId,
                    CriterionId = scoreDto.CriterionId,
                    ErrorMessage = "Invalid criterion ID."
                });
                continue;
            }

            // Validate score range (0-10)
            if (scoreDto.Score < 0 || scoreDto.Score > 10)
            {
                validationErrors.Add(new ScoreValidationError
                {
                    BidderId = scoreDto.BidderId,
                    CriterionId = scoreDto.CriterionId,
                    ErrorMessage = "Score must be between 0 and 10."
                });
                continue;
            }

            // Validate comment requirement for extreme scores
            if ((scoreDto.Score < 3 || scoreDto.Score > 8) &&
                string.IsNullOrWhiteSpace(scoreDto.Comment))
            {
                validationErrors.Add(new ScoreValidationError
                {
                    BidderId = scoreDto.BidderId,
                    CriterionId = scoreDto.CriterionId,
                    ErrorMessage = "Comment is required for scores below 3 or above 8."
                });
                continue;
            }

            // Find existing score or create new
            var existingScore = existingScores.FirstOrDefault(s =>
                s.BidderId == scoreDto.BidderId &&
                s.CriterionId == scoreDto.CriterionId);

            if (existingScore != null)
            {
                // Check if score was already finalized
                if (!existingScore.IsDraft && request.IsFinalSubmission)
                {
                    validationErrors.Add(new ScoreValidationError
                    {
                        BidderId = scoreDto.BidderId,
                        CriterionId = scoreDto.CriterionId,
                        ErrorMessage = "This score has already been finalized."
                    });
                    continue;
                }

                // Update existing score
                existingScore.Score = scoreDto.Score;
                existingScore.Comment = scoreDto.Comment;
                existingScore.IsDraft = !request.IsFinalSubmission;
                if (request.IsFinalSubmission)
                {
                    existingScore.SubmittedAt = now;
                }
            }
            else
            {
                // Create new score
                var newScore = new TechnicalScore
                {
                    Id = Guid.NewGuid(),
                    TenderId = request.TenderId,
                    BidderId = scoreDto.BidderId,
                    PanelistUserId = currentUserId.Value,
                    CriterionId = scoreDto.CriterionId,
                    Score = scoreDto.Score,
                    Comment = scoreDto.Comment,
                    IsDraft = !request.IsFinalSubmission,
                    SubmittedAt = request.IsFinalSubmission ? now : null
                };
                _context.TechnicalScores.Add(newScore);
            }

            scoresSaved++;
        }

        // If there are validation errors and this is a final submission, abort
        if (validationErrors.Any() && request.IsFinalSubmission)
        {
            return new SaveTechnicalScoresResult
            {
                Success = false,
                ErrorMessage = "Cannot finalize scores due to validation errors.",
                ValidationErrors = validationErrors
            };
        }

        await _context.SaveChangesAsync(cancellationToken);

        // Check if panelist has completed all scoring
        if (request.IsFinalSubmission)
        {
            await UpdatePanelistCompletionStatus(
                request.TenderId,
                currentUserId.Value,
                validBidderIds.Count,
                validCriteriaIds.Count,
                cancellationToken);
        }

        _logger.LogInformation(
            "Saved {Count} technical scores for tender {TenderId} by panelist {PanelistId}. Final: {IsFinal}",
            scoresSaved, request.TenderId, currentUserId, request.IsFinalSubmission);

        return new SaveTechnicalScoresResult
        {
            ScoresSaved = scoresSaved,
            IsFinalized = request.IsFinalSubmission,
            Success = true,
            ValidationErrors = validationErrors
        };
    }

    private async Task UpdatePanelistCompletionStatus(
        Guid tenderId,
        Guid panelistUserId,
        int totalBidders,
        int totalCriteria,
        CancellationToken cancellationToken)
    {
        // Count finalized scores
        var finalizedScoreCount = await _context.TechnicalScores
            .CountAsync(s => s.TenderId == tenderId &&
                           s.PanelistUserId == panelistUserId &&
                           !s.IsDraft,
                       cancellationToken);

        var expectedScoreCount = totalBidders * totalCriteria;

        // If all scores are finalized, mark panelist as complete
        if (finalizedScoreCount >= expectedScoreCount)
        {
            var panel = await _context.EvaluationPanels
                .FirstOrDefaultAsync(p => p.TenderId == tenderId &&
                                        p.PanelistUserId == panelistUserId,
                                   cancellationToken);

            if (panel != null && panel.CompletedAt == null)
            {
                panel.CompletedAt = DateTime.UtcNow;
                await _context.SaveChangesAsync(cancellationToken);

                _logger.LogInformation(
                    "Panelist {PanelistId} completed scoring for tender {TenderId}",
                    panelistUserId, tenderId);
            }
        }
    }
}
