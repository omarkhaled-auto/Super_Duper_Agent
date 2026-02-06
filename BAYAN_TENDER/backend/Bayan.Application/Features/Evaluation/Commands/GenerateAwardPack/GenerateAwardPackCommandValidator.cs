using FluentValidation;

namespace Bayan.Application.Features.Evaluation.Commands.GenerateAwardPack;

/// <summary>
/// Validator for GenerateAwardPackCommand.
/// </summary>
public class GenerateAwardPackCommandValidator : AbstractValidator<GenerateAwardPackCommand>
{
    public GenerateAwardPackCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        When(x => !string.IsNullOrEmpty(x.ExecutiveSummary), () =>
        {
            RuleFor(x => x.ExecutiveSummary)
                .MaximumLength(5000)
                .WithMessage("Executive summary cannot exceed 5000 characters.");
        });

        When(x => !string.IsNullOrEmpty(x.RecommendationNotes), () =>
        {
            RuleFor(x => x.RecommendationNotes)
                .MaximumLength(5000)
                .WithMessage("Recommendation notes cannot exceed 5000 characters.");
        });
    }
}
