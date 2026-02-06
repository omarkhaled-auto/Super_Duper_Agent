using FluentValidation;

namespace Bayan.Application.Features.Clarifications.Commands.DraftAnswer;

/// <summary>
/// Validator for the DraftAnswerCommand.
/// </summary>
public class DraftAnswerCommandValidator : AbstractValidator<DraftAnswerCommand>
{
    public DraftAnswerCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.ClarificationId)
            .NotEmpty()
            .WithMessage("Clarification ID is required.");

        RuleFor(x => x.UserId)
            .NotEmpty()
            .WithMessage("User ID is required.");

        RuleFor(x => x.Answer)
            .NotEmpty()
            .WithMessage("Answer is required.")
            .MaximumLength(10000)
            .WithMessage("Answer must not exceed 10000 characters.");
    }
}
