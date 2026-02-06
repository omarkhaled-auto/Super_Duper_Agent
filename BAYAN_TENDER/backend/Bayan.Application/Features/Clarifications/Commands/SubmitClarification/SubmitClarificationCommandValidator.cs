using FluentValidation;

namespace Bayan.Application.Features.Clarifications.Commands.SubmitClarification;

/// <summary>
/// Validator for the SubmitClarificationCommand.
/// </summary>
public class SubmitClarificationCommandValidator : AbstractValidator<SubmitClarificationCommand>
{
    public SubmitClarificationCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidderId)
            .NotEmpty()
            .WithMessage("Bidder ID is required.");

        RuleFor(x => x.Subject)
            .NotEmpty()
            .WithMessage("Subject is required.")
            .MaximumLength(500)
            .WithMessage("Subject must not exceed 500 characters.");

        RuleFor(x => x.Question)
            .NotEmpty()
            .WithMessage("Question is required.")
            .MaximumLength(5000)
            .WithMessage("Question must not exceed 5000 characters.");

        RuleFor(x => x.RelatedBoqSection)
            .MaximumLength(200)
            .When(x => !string.IsNullOrEmpty(x.RelatedBoqSection))
            .WithMessage("Related BOQ section must not exceed 200 characters.");
    }
}
