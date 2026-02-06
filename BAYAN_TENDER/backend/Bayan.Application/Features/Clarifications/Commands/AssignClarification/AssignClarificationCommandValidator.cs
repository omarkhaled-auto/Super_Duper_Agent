using FluentValidation;

namespace Bayan.Application.Features.Clarifications.Commands.AssignClarification;

/// <summary>
/// Validator for the AssignClarificationCommand.
/// </summary>
public class AssignClarificationCommandValidator : AbstractValidator<AssignClarificationCommand>
{
    public AssignClarificationCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.ClarificationId)
            .NotEmpty()
            .WithMessage("Clarification ID is required.");

        RuleFor(x => x.AssignToUserId)
            .NotEmpty()
            .WithMessage("Assign to user ID is required.");

        RuleFor(x => x.AssignedByUserId)
            .NotEmpty()
            .WithMessage("Assigned by user ID is required.");
    }
}
