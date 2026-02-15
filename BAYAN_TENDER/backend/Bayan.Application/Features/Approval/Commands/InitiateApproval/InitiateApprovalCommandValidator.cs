using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Approval.Commands.InitiateApproval;

/// <summary>
/// Validator for InitiateApprovalCommand.
/// </summary>
public class InitiateApprovalCommandValidator : AbstractValidator<InitiateApprovalCommand>
{
    private readonly IApplicationDbContext _context;

    public InitiateApprovalCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.")
            .MustAsync(TenderExists).WithMessage("Tender not found.")
            .MustAsync(TenderInEvaluationStatus).WithMessage("Tender must be in Evaluation status to initiate approval.")
            .MustAsync(NoExistingActiveWorkflow).WithMessage("An active approval workflow already exists for this tender.");

        RuleFor(x => x.NumberOfLevels)
            .Must(x => x == null || (x >= 1 && x <= 10))
            .WithMessage("Number of levels must be between 1 and 10.");

        RuleFor(x => x.ApproverUserIds)
            .NotNull().WithMessage("Approver list is required.")
            .Must((cmd, ids) => ids.Count == (cmd.NumberOfLevels ?? 3))
            .WithMessage(cmd => $"Exactly {cmd.NumberOfLevels ?? 3} approvers must be specified (one per level).")
            .Must(x => x.Distinct().Count() == x.Count).WithMessage("Approver user IDs must be unique.")
            .MustAsync(AllApproversExist).WithMessage("One or more approver users not found.")
            .MustAsync(AllApproversAreActive).WithMessage("One or more approvers are inactive users.");

        RuleFor(x => x.LevelDeadlines)
            .Must((cmd, deadlines) => deadlines == null || deadlines.Count == 0 || deadlines.Count == (cmd.NumberOfLevels ?? 3))
            .WithMessage(cmd => $"If deadlines are specified, exactly {cmd.NumberOfLevels ?? 3} must be provided (one per level).")
            .Must(DeadlinesInFuture)
            .WithMessage("All deadlines must be in the future.");

        RuleFor(x => x)
            .MustAsync(ChangeReasonProvidedWhenApproversDiffer)
            .WithMessage("Reason is required (minimum 10 characters) when changing approvers during re-initiation.");
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders
            .AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> TenderInEvaluationStatus(Guid tenderId, CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == tenderId, cancellationToken);

        return tender?.Status == TenderStatus.Evaluation;
    }

    private async Task<bool> NoExistingActiveWorkflow(Guid tenderId, CancellationToken cancellationToken)
    {
        var existingWorkflow = await _context.ApprovalWorkflows
            .FirstOrDefaultAsync(w => w.TenderId == tenderId, cancellationToken);

        if (existingWorkflow == null)
            return true;

        // Allow if previous workflow was rejected or returned (can re-initiate)
        return existingWorkflow.Status == ApprovalWorkflowStatus.Rejected ||
               existingWorkflow.Status == ApprovalWorkflowStatus.RevisionNeeded;
    }

    private async Task<bool> AllApproversExist(List<Guid> approverIds, CancellationToken cancellationToken)
    {
        if (approverIds == null || !approverIds.Any())
            return true; // Other validation will handle empty list

        var existingCount = await _context.Users
            .CountAsync(u => approverIds.Contains(u.Id), cancellationToken);

        return existingCount == approverIds.Count;
    }

    private async Task<bool> AllApproversAreActive(List<Guid> approverIds, CancellationToken cancellationToken)
    {
        if (approverIds == null || !approverIds.Any())
            return true; // Other validation will handle empty list

        var activeCount = await _context.Users
            .CountAsync(u => approverIds.Contains(u.Id) && u.IsActive, cancellationToken);

        return activeCount == approverIds.Count;
    }

    private bool DeadlinesInFuture(List<DateTime?>? deadlines)
    {
        if (deadlines == null || deadlines.Count == 0)
            return true;

        var now = DateTime.UtcNow;
        return deadlines.All(d => !d.HasValue || d.Value > now);
    }

    private async Task<bool> ChangeReasonProvidedWhenApproversDiffer(
        InitiateApprovalCommand command,
        CancellationToken cancellationToken)
    {
        var expectedCount = command.NumberOfLevels ?? 3;
        if (command.ApproverUserIds == null || command.ApproverUserIds.Count != expectedCount)
            return true;

        var existingWorkflow = await _context.ApprovalWorkflows
            .Include(w => w.Levels)
            .FirstOrDefaultAsync(w => w.TenderId == command.TenderId, cancellationToken);

        if (existingWorkflow == null)
            return true;

        var isReinitiableWorkflow = existingWorkflow.Status == ApprovalWorkflowStatus.Rejected ||
                                    existingWorkflow.Status == ApprovalWorkflowStatus.RevisionNeeded;
        if (!isReinitiableWorkflow)
            return true;

        var previousApproverIds = existingWorkflow.Levels
            .OrderBy(l => l.LevelNumber)
            .Select(l => l.ApproverUserId)
            .ToList();

        if (previousApproverIds.Count != expectedCount)
            return true;

        var approversChanged = !previousApproverIds.SequenceEqual(command.ApproverUserIds);
        if (!approversChanged)
            return true;

        var reason = command.ApproverChangeReason?.Trim();
        return !string.IsNullOrWhiteSpace(reason) && reason.Length >= 10;
    }
}
