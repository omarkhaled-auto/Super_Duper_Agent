using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Approval.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using System.Text.Json;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Approval.Commands.InitiateApproval;

/// <summary>
/// Handler for InitiateApprovalCommand.
/// </summary>
public class InitiateApprovalCommandHandler : IRequestHandler<InitiateApprovalCommand, InitiateApprovalResult>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;
    private readonly IEmailService _emailService;
    private readonly IMapper _mapper;
    private readonly ILogger<InitiateApprovalCommandHandler> _logger;

    public InitiateApprovalCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService,
        IEmailService emailService,
        IMapper mapper,
        ILogger<InitiateApprovalCommandHandler> logger)
    {
        _context = context;
        _currentUserService = currentUserService;
        _emailService = emailService;
        _mapper = mapper;
        _logger = logger;
    }

    public async Task<InitiateApprovalResult> Handle(InitiateApprovalCommand request, CancellationToken cancellationToken)
    {
        var currentUserId = _currentUserService.UserId
            ?? throw new UnauthorizedAccessException("User must be authenticated to initiate approval workflow.");

        // Get tender with client info
        var tender = await _context.Tenders
            .Include(t => t.Client)
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken)
            ?? throw new InvalidOperationException("Tender not found.");

        // Delete any existing rejected/returned workflow for re-initiation
        var existingWorkflow = await _context.ApprovalWorkflows
            .Include(w => w.Levels)
            .FirstOrDefaultAsync(w => w.TenderId == request.TenderId, cancellationToken);

        var previousApproverIds = new List<Guid>();
        var approversChangedOnReinit = false;

        if (existingWorkflow != null)
        {
            previousApproverIds = existingWorkflow.Levels
                .OrderBy(l => l.LevelNumber)
                .Select(l => l.ApproverUserId)
                .ToList();

            approversChangedOnReinit = previousApproverIds.Count == request.ApproverUserIds.Count &&
                !previousApproverIds.SequenceEqual(request.ApproverUserIds);

            _context.ApprovalLevels.RemoveRange(existingWorkflow.Levels);
            _context.ApprovalWorkflows.Remove(existingWorkflow);
            await _context.SaveChangesAsync(cancellationToken);
        }

        // Create new workflow
        var workflow = new ApprovalWorkflow
        {
            Id = Guid.NewGuid(),
            TenderId = request.TenderId,
            Status = ApprovalWorkflowStatus.InProgress,
            InitiatedBy = currentUserId,
            InitiatedAt = DateTime.UtcNow,
            AwardPackPdfPath = request.AwardPackPdfPath,
            CreatedAt = DateTime.UtcNow
        };

        _context.ApprovalWorkflows.Add(workflow);

        // Create approval levels (sequential, 3 levels)
        var approverUsers = await _context.Users
            .Where(u => request.ApproverUserIds.Contains(u.Id))
            .ToDictionaryAsync(u => u.Id, cancellationToken);

        var levels = new List<ApprovalLevel>();
        for (int i = 0; i < 3; i++)
        {
            var level = new ApprovalLevel
            {
                Id = Guid.NewGuid(),
                WorkflowId = workflow.Id,
                LevelNumber = i + 1,
                ApproverUserId = request.ApproverUserIds[i],
                Deadline = request.LevelDeadlines?.ElementAtOrDefault(i),
                Status = i == 0 ? ApprovalLevelStatus.Active : ApprovalLevelStatus.Waiting,
                NotifiedAt = i == 0 ? DateTime.UtcNow : null,
                CreatedAt = DateTime.UtcNow
            };
            levels.Add(level);
            _context.ApprovalLevels.Add(level);
        }

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Created approval workflow {WorkflowId} for tender {TenderId} with 3 levels. Initiated by user {UserId}",
            workflow.Id, request.TenderId, currentUserId);

        // Send notification to Level 1 approver
        var level1NotificationSent = false;
        var level1Approver = approverUsers[request.ApproverUserIds[0]];
        var initiator = await _context.Users.FirstOrDefaultAsync(u => u.Id == currentUserId, cancellationToken);

        if (approversChangedOnReinit)
        {
            var auditLog = new AuditLog
            {
                Id = Guid.NewGuid(),
                UserId = currentUserId,
                UserEmail = initiator?.Email,
                Action = "Approval.ReinitApproversChanged",
                EntityType = "ApprovalWorkflow",
                EntityId = workflow.Id,
                OldValues = JsonSerializer.Serialize(new
                {
                    approverUserIds = previousApproverIds
                }),
                NewValues = JsonSerializer.Serialize(new
                {
                    approverUserIds = request.ApproverUserIds,
                    reason = request.ApproverChangeReason?.Trim()
                }),
                CreatedAt = DateTime.UtcNow
            };

            _context.AuditLogs.Add(auditLog);
            await _context.SaveChangesAsync(cancellationToken);
        }

        try
        {
            await _emailService.SendApprovalRequestEmailAsync(
                level1Approver.Email,
                level1Approver.FirstName,
                tender.Title,
                tender.Reference,
                initiator?.FullName ?? "Unknown",
                1, // Level number
                levels[0].Deadline,
                cancellationToken);

            level1NotificationSent = true;
            _logger.LogInformation(
                "Sent Level 1 approval request email to {Email} for workflow {WorkflowId}",
                level1Approver.Email, workflow.Id);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex,
                "Failed to send Level 1 approval request email to {Email} for workflow {WorkflowId}",
                level1Approver.Email, workflow.Id);
        }

        // Build response DTO
        var workflowDto = new ApprovalWorkflowDto
        {
            Id = workflow.Id,
            TenderId = tender.Id,
            TenderReference = tender.Reference,
            TenderTitle = tender.Title,
            Status = workflow.Status,
            InitiatedBy = workflow.InitiatedBy,
            InitiatedByName = initiator?.FullName ?? "Unknown",
            InitiatedAt = workflow.InitiatedAt,
            CompletedAt = workflow.CompletedAt,
            AwardPackPdfPath = workflow.AwardPackPdfPath,
            CurrentLevel = 1,
            TotalLevels = 3,
            Levels = levels.Select(l => new ApprovalLevelDto
            {
                Id = l.Id,
                WorkflowId = l.WorkflowId,
                LevelNumber = l.LevelNumber,
                ApproverUserId = l.ApproverUserId,
                ApproverName = approverUsers[l.ApproverUserId].FullName,
                ApproverEmail = approverUsers[l.ApproverUserId].Email,
                Deadline = l.Deadline,
                Decision = l.Decision,
                DecisionComment = l.DecisionComment,
                DecidedAt = l.DecidedAt,
                Status = l.Status,
                NotifiedAt = l.NotifiedAt
            }).ToList()
        };

        return new InitiateApprovalResult
        {
            WorkflowId = workflow.Id,
            Workflow = workflowDto,
            Level1NotificationSent = level1NotificationSent
        };
    }
}
