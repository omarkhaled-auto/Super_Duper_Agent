using FluentValidation;

namespace Bayan.Application.Features.Addenda.Commands.CreateAddendum;

/// <summary>
/// Validator for the CreateAddendumCommand.
/// </summary>
public class CreateAddendumCommandValidator : AbstractValidator<CreateAddendumCommand>
{
    public CreateAddendumCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.Summary)
            .NotEmpty()
            .WithMessage("Addendum summary is required.")
            .MaximumLength(5000)
            .WithMessage("Summary must not exceed 5000 characters.");

        RuleFor(x => x.NewDeadline)
            .NotNull()
            .When(x => x.ExtendsDeadline)
            .WithMessage("New deadline is required when extending the deadline.");

        RuleFor(x => x.NewDeadline)
            .GreaterThan(DateTime.UtcNow)
            .When(x => x.ExtendsDeadline && x.NewDeadline.HasValue)
            .WithMessage("New deadline must be in the future.");
    }
}
