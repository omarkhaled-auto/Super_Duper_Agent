using FluentValidation;

namespace Bayan.Application.Features.Clarifications.Commands.MarkDuplicate;

/// <summary>
/// Validator for the MarkDuplicateCommand.
/// </summary>
public class MarkDuplicateCommandValidator : AbstractValidator<MarkDuplicateCommand>
{
    public MarkDuplicateCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.ClarificationId)
            .NotEmpty()
            .WithMessage("Clarification ID is required.");

        RuleFor(x => x.OriginalClarificationId)
            .NotEmpty()
            .WithMessage("Original clarification ID is required.");

        RuleFor(x => x.UserId)
            .NotEmpty()
            .WithMessage("User ID is required.");

        RuleFor(x => x)
            .Must(x => x.ClarificationId != x.OriginalClarificationId)
            .WithMessage("A clarification cannot be marked as a duplicate of itself.");
    }
}
