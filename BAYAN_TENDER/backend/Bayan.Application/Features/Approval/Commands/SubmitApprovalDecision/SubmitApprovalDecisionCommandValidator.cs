using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Approval.Commands.SubmitApprovalDecision;

/// <summary>
/// Validator for SubmitApprovalDecisionCommand.
/// </summary>
public class SubmitApprovalDecisionCommandValidator : AbstractValidator<SubmitApprovalDecisionCommand>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public SubmitApprovalDecisionCommandValidator(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;

        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.")
            .MustAsync(HaveActiveWorkflow).WithMessage("No active approval workflow found for this tender.")
            .MustAsync(CurrentUserIsActiveApprover).WithMessage("You are not authorized to approve at the current level.");

        RuleFor(x => x.Decision)
            .IsInEnum().WithMessage("Invalid decision specified.");

        RuleFor(x => x.Comment)
            .NotEmpty().WithMessage("Comment is required when rejecting or returning for revision.")
            .When(x => x.Decision == ApprovalDecision.Reject || x.Decision == ApprovalDecision.ReturnForRevision);

        RuleFor(x => x.Comment)
            .MaximumLength(2000).WithMessage("Comment must not exceed 2000 characters.")
            .When(x => !string.IsNullOrEmpty(x.Comment));
    }

    private async Task<bool> HaveActiveWorkflow(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.ApprovalWorkflows
            .AnyAsync(w => w.TenderId == tenderId && w.Status == ApprovalWorkflowStatus.InProgress, cancellationToken);
    }

    private async Task<bool> CurrentUserIsActiveApprover(Guid tenderId, CancellationToken cancellationToken)
    {
        var currentUserId = _currentUserService.UserId;
        if (!currentUserId.HasValue)
            return false;

        var workflow = await _context.ApprovalWorkflows
            .Include(w => w.Levels)
            .FirstOrDefaultAsync(w => w.TenderId == tenderId && w.Status == ApprovalWorkflowStatus.InProgress, cancellationToken);

        if (workflow == null)
            return false;

        var activeLevel = workflow.Levels.FirstOrDefault(l => l.Status == ApprovalLevelStatus.Active);
        if (activeLevel == null)
            return false;

        return activeLevel.ApproverUserId == currentUserId.Value;
    }
}
