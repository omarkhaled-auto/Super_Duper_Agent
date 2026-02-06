using FluentValidation;

namespace Bayan.Application.Features.Clarifications.Commands.SubmitInternalRfi;

/// <summary>
/// Validator for the SubmitInternalRfiCommand.
/// </summary>
public class SubmitInternalRfiCommandValidator : AbstractValidator<SubmitInternalRfiCommand>
{
    public SubmitInternalRfiCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.UserId)
            .NotEmpty()
            .WithMessage("User ID is required.");

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

        RuleFor(x => x.Priority)
            .IsInEnum()
            .WithMessage("Invalid priority value.");
    }
}
