using FluentValidation;

namespace Bayan.Application.Features.Evaluation.Commands.CalculateCommercialScores;

/// <summary>
/// Validator for CalculateCommercialScoresCommand.
/// </summary>
public class CalculateCommercialScoresCommandValidator : AbstractValidator<CalculateCommercialScoresCommand>
{
    public CalculateCommercialScoresCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");
    }
}
