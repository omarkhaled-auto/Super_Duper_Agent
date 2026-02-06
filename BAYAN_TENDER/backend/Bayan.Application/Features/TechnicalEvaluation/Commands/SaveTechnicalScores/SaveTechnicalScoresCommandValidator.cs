using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Commands.SaveTechnicalScores;

/// <summary>
/// Validator for SaveTechnicalScoresCommand.
/// </summary>
public class SaveTechnicalScoresCommandValidator : AbstractValidator<SaveTechnicalScoresCommand>
{
    private readonly IApplicationDbContext _context;

    public SaveTechnicalScoresCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.")
            .MustAsync(TenderExists).WithMessage("Tender not found.")
            .MustAsync(EvaluationSetupExists).WithMessage("Evaluation setup not found for this tender.")
            .MustAsync(TechnicalScoresNotLocked).WithMessage("Technical scores are locked and cannot be modified.");

        RuleFor(x => x.Scores)
            .NotEmpty().WithMessage("At least one score must be provided.");

        RuleForEach(x => x.Scores).ChildRules(score =>
        {
            score.RuleFor(s => s.BidderId)
                .NotEmpty().WithMessage("Bidder ID is required.");

            score.RuleFor(s => s.CriterionId)
                .NotEmpty().WithMessage("Criterion ID is required.");

            score.RuleFor(s => s.Score)
                .InclusiveBetween(0, 10).WithMessage("Score must be between 0 and 10.");

            score.RuleFor(s => s.Comment)
                .NotEmpty()
                .When(s => s.Score < 3 || s.Score > 8)
                .WithMessage("Comment is required for scores below 3 or above 8.");
        });
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> EvaluationSetupExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.EvaluationStates.AnyAsync(e => e.TenderId == tenderId, cancellationToken);
    }

    private async Task<bool> TechnicalScoresNotLocked(Guid tenderId, CancellationToken cancellationToken)
    {
        var evaluationState = await _context.EvaluationStates
            .FirstOrDefaultAsync(e => e.TenderId == tenderId, cancellationToken);

        return evaluationState == null || !evaluationState.TechnicalScoresLocked;
    }
}
