using FluentValidation;

namespace Bayan.Application.Features.Evaluation.Commands.CalculateCombinedScores;

/// <summary>
/// Validator for CalculateCombinedScoresCommand.
/// </summary>
public class CalculateCombinedScoresCommandValidator : AbstractValidator<CalculateCombinedScoresCommand>
{
    public CalculateCombinedScoresCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        When(x => x.TechnicalWeight.HasValue, () =>
        {
            RuleFor(x => x.TechnicalWeight!.Value)
                .InclusiveBetween(0, 100)
                .WithMessage("Technical weight must be between 0 and 100.");
        });

        When(x => x.CommercialWeight.HasValue, () =>
        {
            RuleFor(x => x.CommercialWeight!.Value)
                .InclusiveBetween(0, 100)
                .WithMessage("Commercial weight must be between 0 and 100.");
        });

        When(x => x.TechnicalWeight.HasValue && x.CommercialWeight.HasValue, () =>
        {
            RuleFor(x => x)
                .Must(x => x.TechnicalWeight!.Value + x.CommercialWeight!.Value == 100)
                .WithMessage("Technical and commercial weights must sum to 100.");
        });
    }
}
