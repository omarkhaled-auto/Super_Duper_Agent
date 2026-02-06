using FluentValidation;

namespace Bayan.Application.Features.BidAnalysis.Commands.UpdateManualMatch;

/// <summary>
/// Validator for UpdateManualMatchCommand.
/// </summary>
public class UpdateManualMatchCommandValidator : AbstractValidator<UpdateManualMatchCommand>
{
    public UpdateManualMatchCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidId)
            .NotEmpty()
            .WithMessage("Bid ID is required.");

        RuleFor(x => x.ItemId)
            .NotEmpty()
            .WithMessage("Item ID is required.");

        RuleFor(x => x.BoqItemId)
            .NotEmpty()
            .WithMessage("BOQ Item ID is required.");

        RuleFor(x => x.Notes)
            .MaximumLength(1000)
            .When(x => !string.IsNullOrEmpty(x.Notes))
            .WithMessage("Notes cannot exceed 1000 characters.");
    }
}
