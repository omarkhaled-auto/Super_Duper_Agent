using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Approval.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Approval.Commands.SubmitApprovalDecision;

/// <summary>
/// Handler for SubmitApprovalDecisionCommand.
/// </summary>
public class SubmitApprovalDecisionCommandHandler : IRequestHandler<SubmitApprovalDecisionCommand, SubmitApprovalDecisionResult>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;
    private readonly IEmailService _emailService;
    private readonly IMapper _mapper;
    private readonly ILogger<SubmitApprovalDecisionCommandHandler> _logger;

    public SubmitApprovalDecisionCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService,
        IEmailService emailService,
        IMapper mapper,
        ILogger<SubmitApprovalDecisionCommandHandler> logger)
    {
        _context = context;
        _currentUserService = currentUserService;
        _emailService = emailService;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<SubmitApprovalDecisionResult> Handle(SubmitApprovalDecisionCommand request, CancellationToken cancellationToken)
    {
        var currentUserId = _currentUserService.UserId
            ?? throw new UnauthorizedAccessException("User must be authenticated to submit approval decision.");

        // Get workflow with all related data
        var workflow = await _context.ApprovalWorkflows
            .Include(w => w.Levels)
            .Include(w => w.Tender)
                .ThenInclude(t => t.Client)
            .Include(w => w.Initiator)
            .FirstOrDefaultAsync(w => w.TenderId == request.TenderId && w.Status == ApprovalWorkflowStatus.InProgress, cancellationToken)
            ?? throw new InvalidOperationException("No active approval workflow found for this tender.");

        // Get the active level
        var activeLevel = workflow.Levels
            .OrderBy(l => l.LevelNumber)
            .FirstOrDefault(l => l.Status == ApprovalLevelStatus.Active)
            ?? throw new InvalidOperationException("No active approval level found.");

        // Verify current user is the approver
        if (activeLevel.ApproverUserId != currentUserId)
            throw new UnauthorizedAccessException("You are not authorized to approve at the current level.");

        // Get approver users for DTOs
        var approverUserIds = workflow.Levels.Select(l => l.ApproverUserId).ToList();
        var approverUsers = await _context.Users
            .Where(u => approverUserIds.Contains(u.Id))
            .ToDictionaryAsync(u => u.Id, cancellationToken);

        var currentApprover = approverUsers[currentUserId];

        // Record the decision
        activeLevel.Decision = request.Decision;
        activeLevel.DecisionComment = request.Comment;
        activeLevel.DecidedAt = DateTime.UtcNow;
        activeLevel.UpdatedAt = DateTime.UtcNow;

        string message;
        bool isWorkflowComplete = false;
        bool notificationSent = false;

        switch (request.Decision)
        {
            case ApprovalDecision.Approve:
                activeLevel.Status = ApprovalLevelStatus.Approved;
                (message, isWorkflowComplete, notificationSent) = await HandleApprovalAsync(
                    workflow, activeLevel, approverUsers, cancellationToken);
                break;

            case ApprovalDecision.Reject:
                activeLevel.Status = ApprovalLevelStatus.Rejected;
                (message, notificationSent) = await HandleRejectionAsync(
                    workflow, activeLevel, cancellationToken);
                isWorkflowComplete = true;
                break;

            case ApprovalDecision.ReturnForRevision:
                activeLevel.Status = ApprovalLevelStatus.Returned;
                (message, notificationSent) = await HandleReturnForRevisionAsync(
                    workflow, activeLevel, cancellationToken);
                isWorkflowComplete = true;
                break;

            default:
                throw new InvalidOperationException("Invalid approval decision.");
        }

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Approval decision recorded: {Decision} by user {UserId} for workflow {WorkflowId} level {LevelNumber}",
            request.Decision, currentUserId, workflow.Id, activeLevel.LevelNumber);

        // Build response DTO
        var workflowDto = BuildWorkflowDto(workflow, approverUsers);

        return new SubmitApprovalDecisionResult
        {
            Success = true,
            Workflow = workflowDto,
            Message = message,
            IsWorkflowComplete = isWorkflowComplete,
            NotificationSent = notificationSent
        };
    }

    private async Task<(string message, bool isComplete, bool notificationSent)> HandleApprovalAsync(
        Domain.Entities.ApprovalWorkflow workflow,
        Domain.Entities.ApprovalLevel activeLevel,
        Dictionary<Guid, Domain.Entities.User> approverUsers,
        CancellationToken cancellationToken)
    {
        var nextLevel = workflow.Levels
            .OrderBy(l => l.LevelNumber)
            .FirstOrDefault(l => l.LevelNumber == activeLevel.LevelNumber + 1);

        bool notificationSent = false;

        if (nextLevel != null)
        {
            // Progress to next level
            nextLevel.Status = ApprovalLevelStatus.Active;
            nextLevel.NotifiedAt = DateTime.UtcNow;
            nextLevel.UpdatedAt = DateTime.UtcNow;

            // Send notification to next approver
            var nextApprover = approverUsers[nextLevel.ApproverUserId];
            try
            {
                await _emailService.SendApprovalRequestEmailAsync(
                    nextApprover.Email,
                    nextApprover.FirstName,
                    workflow.Tender.Title,
                    workflow.Tender.Reference,
                    workflow.Initiator.FullName,
                    nextLevel.LevelNumber,
                    nextLevel.Deadline,
                    cancellationToken);

                notificationSent = true;
                _logger.LogInformation(
                    "Sent Level {Level} approval request email to {Email} for workflow {WorkflowId}",
                    nextLevel.LevelNumber, nextApprover.Email, workflow.Id);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex,
                    "Failed to send Level {Level} approval request email to {Email} for workflow {WorkflowId}",
                    nextLevel.LevelNumber, nextApprover.Email, workflow.Id);
            }

            return ($"Approved. Workflow progressed to Level {nextLevel.LevelNumber}.", false, notificationSent);
        }
        else
        {
            // Final approval - workflow complete
            workflow.Status = ApprovalWorkflowStatus.Approved;
            workflow.CompletedAt = DateTime.UtcNow;
            workflow.UpdatedAt = DateTime.UtcNow;

            // Update tender status to Awarded
            workflow.Tender.Status = TenderStatus.Awarded;
            workflow.Tender.AwardedAt = DateTime.UtcNow;
            workflow.Tender.UpdatedAt = DateTime.UtcNow;

            // Send award notification to initiator
            try
            {
                await _emailService.SendAwardNotificationEmailAsync(
                    workflow.Initiator.Email,
                    workflow.Initiator.FirstName,
                    workflow.Tender.Title,
                    workflow.Tender.Reference,
                    cancellationToken);

                notificationSent = true;
                _logger.LogInformation(
                    "Sent award notification email to {Email} for tender {TenderReference}",
                    workflow.Initiator.Email, workflow.Tender.Reference);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex,
                    "Failed to send award notification email to {Email} for tender {TenderReference}",
                    workflow.Initiator.Email, workflow.Tender.Reference);
            }

            _logger.LogInformation(
                "Approval workflow {WorkflowId} completed. Tender {TenderId} status set to Awarded.",
                workflow.Id, workflow.TenderId);

            return ("Final approval granted. Tender has been awarded.", true, notificationSent);
        }
    }

    private async Task<(string message, bool notificationSent)> HandleRejectionAsync(
        Domain.Entities.ApprovalWorkflow workflow,
        Domain.Entities.ApprovalLevel activeLevel,
        CancellationToken cancellationToken)
    {
        workflow.Status = ApprovalWorkflowStatus.Rejected;
        workflow.CompletedAt = DateTime.UtcNow;
        workflow.UpdatedAt = DateTime.UtcNow;

        // Mark all remaining levels as rejected
        foreach (var level in workflow.Levels.Where(l => l.Status == ApprovalLevelStatus.Waiting))
        {
            level.Status = ApprovalLevelStatus.Rejected;
            level.UpdatedAt = DateTime.UtcNow;
        }

        bool notificationSent = false;

        // Send rejection notification to initiator
        try
        {
            await _emailService.SendApprovalDecisionEmailAsync(
                workflow.Initiator.Email,
                workflow.Initiator.FirstName,
                workflow.Tender.Title,
                workflow.Tender.Reference,
                "Rejected",
                activeLevel.LevelNumber,
                activeLevel.DecisionComment,
                cancellationToken);

            notificationSent = true;
            _logger.LogInformation(
                "Sent rejection notification email to {Email} for workflow {WorkflowId}",
                workflow.Initiator.Email, workflow.Id);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex,
                "Failed to send rejection notification email to {Email} for workflow {WorkflowId}",
                workflow.Initiator.Email, workflow.Id);
        }

        return ($"Approval rejected at Level {activeLevel.LevelNumber}. Workflow has been terminated.", notificationSent);
    }

    private async Task<(string message, bool notificationSent)> HandleReturnForRevisionAsync(
        Domain.Entities.ApprovalWorkflow workflow,
        Domain.Entities.ApprovalLevel activeLevel,
        CancellationToken cancellationToken)
    {
        workflow.Status = ApprovalWorkflowStatus.RevisionNeeded;
        workflow.CompletedAt = DateTime.UtcNow;
        workflow.UpdatedAt = DateTime.UtcNow;

        // Mark all remaining levels as returned
        foreach (var level in workflow.Levels.Where(l => l.Status == ApprovalLevelStatus.Waiting))
        {
            level.Status = ApprovalLevelStatus.Returned;
            level.UpdatedAt = DateTime.UtcNow;
        }

        bool notificationSent = false;

        // Send return for revision notification to initiator (TM)
        try
        {
            await _emailService.SendApprovalDecisionEmailAsync(
                workflow.Initiator.Email,
                workflow.Initiator.FirstName,
                workflow.Tender.Title,
                workflow.Tender.Reference,
                "Returned for Revision",
                activeLevel.LevelNumber,
                activeLevel.DecisionComment,
                cancellationToken);

            notificationSent = true;
            _logger.LogInformation(
                "Sent return for revision notification email to {Email} for workflow {WorkflowId}",
                workflow.Initiator.Email, workflow.Id);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex,
                "Failed to send return for revision notification email to {Email} for workflow {WorkflowId}",
                workflow.Initiator.Email, workflow.Id);
        }

        return ($"Returned for revision at Level {activeLevel.LevelNumber}. Tender Manager has been notified.", notificationSent);
    }

    private ApprovalWorkflowDto BuildWorkflowDto(
        Domain.Entities.ApprovalWorkflow workflow,
        Dictionary<Guid, Domain.Entities.User> approverUsers)
    {
        var currentLevel = workflow.Levels
            .OrderBy(l => l.LevelNumber)
            .FirstOrDefault(l => l.Status == ApprovalLevelStatus.Active)?.LevelNumber ??
            workflow.Levels.Max(l => l.LevelNumber);

        return new ApprovalWorkflowDto
        {
            Id = workflow.Id,
            TenderId = workflow.TenderId,
            TenderReference = workflow.Tender.Reference,
            TenderTitle = workflow.Tender.Title,
            Status = workflow.Status,
            InitiatedBy = workflow.InitiatedBy,
            InitiatedByName = workflow.Initiator.FullName,
            InitiatedAt = workflow.InitiatedAt,
            CompletedAt = workflow.CompletedAt,
            AwardPackPdfPath = workflow.AwardPackPdfPath,
            CurrentLevel = currentLevel,
            TotalLevels = workflow.Levels.Count,
            Levels = workflow.Levels
                .OrderBy(l => l.LevelNumber)
                .Select(l => new ApprovalLevelDto
                {
                    Id = l.Id,
                    WorkflowId = l.WorkflowId,
                    LevelNumber = l.LevelNumber,
                    ApproverUserId = l.ApproverUserId,
                    ApproverName = approverUsers.TryGetValue(l.ApproverUserId, out var user) ? user.FullName : "Unknown",
                    ApproverEmail = approverUsers.TryGetValue(l.ApproverUserId, out user) ? user.Email : "Unknown",
                    Deadline = l.Deadline,
                    Decision = l.Decision,
                    DecisionComment = l.DecisionComment,
                    DecidedAt = l.DecidedAt,
                    Status = l.Status,
                    NotifiedAt = l.NotifiedAt
                }).ToList()
        };
    }
}
