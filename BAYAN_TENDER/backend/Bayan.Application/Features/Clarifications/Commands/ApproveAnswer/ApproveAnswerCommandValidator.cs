using FluentValidation;

namespace Bayan.Application.Features.Clarifications.Commands.ApproveAnswer;

/// <summary>
/// Validator for the ApproveAnswerCommand.
/// </summary>
public class ApproveAnswerCommandValidator : AbstractValidator<ApproveAnswerCommand>
{
    public ApproveAnswerCommandValidator()
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
    }
}
