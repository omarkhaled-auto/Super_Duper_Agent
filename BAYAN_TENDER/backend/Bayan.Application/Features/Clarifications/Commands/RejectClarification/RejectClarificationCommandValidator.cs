using FluentValidation;

namespace Bayan.Application.Features.Clarifications.Commands.RejectClarification;

/// <summary>
/// Validator for the RejectClarificationCommand.
/// </summary>
public class RejectClarificationCommandValidator : AbstractValidator<RejectClarificationCommand>
{
    public RejectClarificationCommandValidator()
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

        RuleFor(x => x.Reason)
            .NotEmpty()
            .WithMessage("Rejection reason is required.")
            .MaximumLength(2000)
            .WithMessage("Rejection reason must not exceed 2000 characters.");
    }
}
