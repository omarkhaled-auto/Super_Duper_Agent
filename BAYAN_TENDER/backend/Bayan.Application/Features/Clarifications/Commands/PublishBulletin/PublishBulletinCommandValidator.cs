using FluentValidation;

namespace Bayan.Application.Features.Clarifications.Commands.PublishBulletin;

/// <summary>
/// Validator for the PublishBulletinCommand.
/// </summary>
public class PublishBulletinCommandValidator : AbstractValidator<PublishBulletinCommand>
{
    public PublishBulletinCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.ClarificationIds)
            .NotEmpty()
            .WithMessage("At least one clarification must be selected for the bulletin.");

        RuleFor(x => x.ClarificationIds)
            .Must(ids => ids.Distinct().Count() == ids.Count)
            .WithMessage("Duplicate clarification IDs are not allowed.");

        RuleFor(x => x.Introduction)
            .MaximumLength(2000)
            .WithMessage("Introduction cannot exceed 2000 characters.");

        RuleFor(x => x.ClosingNotes)
            .MaximumLength(2000)
            .WithMessage("Closing notes cannot exceed 2000 characters.");
    }
}
