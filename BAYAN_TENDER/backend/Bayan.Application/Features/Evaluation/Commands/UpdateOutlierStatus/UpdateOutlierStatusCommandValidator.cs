using FluentValidation;

namespace Bayan.Application.Features.Evaluation.Commands.UpdateOutlierStatus;

/// <summary>
/// Validator for UpdateOutlierStatusCommand.
/// </summary>
public class UpdateOutlierStatusCommandValidator : AbstractValidator<UpdateOutlierStatusCommand>
{
    public UpdateOutlierStatusCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.HighThreshold)
            .GreaterThan(0)
            .WithMessage("High threshold must be greater than 0.")
            .GreaterThan(x => x.MediumThreshold)
            .WithMessage("High threshold must be greater than medium threshold.");

        RuleFor(x => x.MediumThreshold)
            .GreaterThan(0)
            .WithMessage("Medium threshold must be greater than 0.");
    }
}
