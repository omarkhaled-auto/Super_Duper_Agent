using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Commands.SetupTechnicalEvaluation;

/// <summary>
/// Validator for SetupTechnicalEvaluationCommand.
/// </summary>
public class SetupTechnicalEvaluationCommandValidator : AbstractValidator<SetupTechnicalEvaluationCommand>
{
    private readonly IApplicationDbContext _context;

    public SetupTechnicalEvaluationCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.")
            .MustAsync(TenderExists).WithMessage("Tender not found.")
            .MustAsync(TenderNotLocked).WithMessage("Technical evaluation scores are already locked for this tender.");

        RuleFor(x => x.ScoringMethod)
            .IsInEnum().WithMessage("Invalid scoring method.");

        RuleFor(x => x.TechnicalEvaluationDeadline)
            .Must(BeInFuture).WithMessage("Technical evaluation deadline must be in the future.")
            .When(x => x.TechnicalEvaluationDeadline.HasValue);

        RuleFor(x => x.PanelistUserIds)
            .NotEmpty().WithMessage("At least one panelist must be assigned.")
            .Must(HaveNoDuplicates).WithMessage("Duplicate panelist IDs are not allowed.");

        RuleForEach(x => x.PanelistUserIds)
            .NotEmpty().WithMessage("Panelist user ID cannot be empty.")
            .MustAsync(UserExists).WithMessage("One or more panelist users do not exist or are inactive.");
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> TenderNotLocked(Guid tenderId, CancellationToken cancellationToken)
    {
        var evaluationState = await _context.EvaluationStates
            .FirstOrDefaultAsync(e => e.TenderId == tenderId, cancellationToken);

        // If no evaluation state exists yet, it's not locked
        if (evaluationState == null)
            return true;

        return !evaluationState.TechnicalScoresLocked;
    }

    private bool BeInFuture(DateTime? deadline)
    {
        return !deadline.HasValue || deadline.Value > DateTime.UtcNow;
    }

    private bool HaveNoDuplicates(List<Guid> panelistIds)
    {
        return panelistIds.Distinct().Count() == panelistIds.Count;
    }

    private async Task<bool> UserExists(Guid userId, CancellationToken cancellationToken)
    {
        return await _context.Users.AnyAsync(u => u.Id == userId && u.IsActive, cancellationToken);
    }
}
