using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.TechnicalEvaluation.Commands.SetupTechnicalEvaluation;

/// <summary>
/// Handler for SetupTechnicalEvaluationCommand.
/// </summary>
public class SetupTechnicalEvaluationCommandHandler
    : IRequestHandler<SetupTechnicalEvaluationCommand, SetupTechnicalEvaluationResult>
{
    private readonly IApplicationDbContext _context;
    private readonly IEmailService _emailService;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<SetupTechnicalEvaluationCommandHandler> _logger;

    public SetupTechnicalEvaluationCommandHandler(
        IApplicationDbContext context,
        IEmailService emailService,
        ICurrentUserService currentUserService,
        ILogger<SetupTechnicalEvaluationCommandHandler> logger)
    {
        _context = context;
        _emailService = emailService;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<SetupTechnicalEvaluationResult> Handle(
        SetupTechnicalEvaluationCommand request,
        CancellationToken cancellationToken)
    {
        // Get the tender with related data
        var tender = await _context.Tenders
            .Include(t => t.EvaluationState)
            .Include(t => t.EvaluationPanels)
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            return new SetupTechnicalEvaluationResult
            {
                Success = false,
                ErrorMessage = $"Tender with ID {request.TenderId} not found."
            };
        }

        // Check if evaluation state already exists
        EvaluationState evaluationState;
        if (tender.EvaluationState != null)
        {
            // Update existing evaluation state
            evaluationState = tender.EvaluationState;
            evaluationState.ScoringMethod = request.ScoringMethod;
            evaluationState.BlindMode = request.BlindMode;
            evaluationState.TechnicalEvaluationDeadline = request.TechnicalEvaluationDeadline;

            _logger.LogInformation(
                "Updating evaluation state for tender {TenderId}",
                request.TenderId);
        }
        else
        {
            // Create new evaluation state
            evaluationState = new EvaluationState
            {
                Id = Guid.NewGuid(),
                TenderId = request.TenderId,
                ScoringMethod = request.ScoringMethod,
                BlindMode = request.BlindMode,
                TechnicalEvaluationDeadline = request.TechnicalEvaluationDeadline,
                TechnicalScoresLocked = false,
                CommercialScoresCalculated = false,
                CombinedScoresCalculated = false
            };

            _context.EvaluationStates.Add(evaluationState);
            _logger.LogInformation(
                "Created new evaluation state {EvaluationStateId} for tender {TenderId}",
                evaluationState.Id, request.TenderId);
        }

        // Get panelist users
        var panelistUsers = await _context.Users
            .Where(u => request.PanelistUserIds.Contains(u.Id) && u.IsActive)
            .ToListAsync(cancellationToken);

        // Get existing panelists for this tender
        var existingPanelistIds = tender.EvaluationPanels.Select(p => p.PanelistUserId).ToHashSet();

        // Create new panel records for new panelists
        var newPanelists = new List<EvaluationPanel>();
        var assignedAt = DateTime.UtcNow;

        foreach (var userId in request.PanelistUserIds)
        {
            if (!existingPanelistIds.Contains(userId))
            {
                var panel = new EvaluationPanel
                {
                    Id = Guid.NewGuid(),
                    TenderId = request.TenderId,
                    PanelistUserId = userId,
                    AssignedAt = assignedAt,
                    CompletedAt = null
                };
                newPanelists.Add(panel);
                _context.EvaluationPanels.Add(panel);
            }
        }

        // Remove panelists no longer in the list (only if they haven't scored anything)
        var panelistsToRemove = tender.EvaluationPanels
            .Where(p => !request.PanelistUserIds.Contains(p.PanelistUserId))
            .ToList();

        foreach (var panelist in panelistsToRemove)
        {
            var hasScores = await _context.TechnicalScores
                .AnyAsync(s => s.TenderId == request.TenderId &&
                              s.PanelistUserId == panelist.PanelistUserId,
                         cancellationToken);

            if (!hasScores)
            {
                _context.EvaluationPanels.Remove(panelist);
                _logger.LogInformation(
                    "Removed panelist {PanelistUserId} from tender {TenderId}",
                    panelist.PanelistUserId, request.TenderId);
            }
        }

        await _context.SaveChangesAsync(cancellationToken);

        // Send notification emails to new panelists
        var notificationsSent = 0;
        var failedNotifications = new List<string>();

        if (request.SendNotificationEmails && newPanelists.Any())
        {
            foreach (var panel in newPanelists)
            {
                var user = panelistUsers.FirstOrDefault(u => u.Id == panel.PanelistUserId);
                if (user == null) continue;

                try
                {
                    var mergeFields = new Dictionary<string, string>
                    {
                        { "FirstName", user.FirstName },
                        { "TenderTitle", tender.Title },
                        { "TenderReference", tender.Reference },
                        { "Deadline", request.TechnicalEvaluationDeadline?.ToString("yyyy-MM-dd HH:mm UTC") ?? "Not specified" }
                    };

                    await _emailService.SendTemplatedEmailAsync(
                        user.Email,
                        "PanelistAssignment",
                        mergeFields,
                        cancellationToken);

                    notificationsSent++;
                    _logger.LogInformation(
                        "Sent panelist assignment notification to {Email} for tender {TenderId}",
                        user.Email, request.TenderId);
                }
                catch (Exception ex)
                {
                    failedNotifications.Add(user.Email);
                    _logger.LogWarning(ex,
                        "Failed to send panelist assignment notification to {Email} for tender {TenderId}",
                        user.Email, request.TenderId);
                }
            }
        }

        return new SetupTechnicalEvaluationResult
        {
            EvaluationStateId = evaluationState.Id,
            TenderId = request.TenderId,
            PanelistsAssigned = request.PanelistUserIds.Count,
            NotificationsSent = notificationsSent,
            FailedNotifications = failedNotifications,
            Success = true
        };
    }
}
