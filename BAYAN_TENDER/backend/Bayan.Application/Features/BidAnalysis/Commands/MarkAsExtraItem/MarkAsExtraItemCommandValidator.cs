using FluentValidation;

namespace Bayan.Application.Features.BidAnalysis.Commands.MarkAsExtraItem;

/// <summary>
/// Validator for MarkAsExtraItemCommand.
/// </summary>
public class MarkAsExtraItemCommandValidator : AbstractValidator<MarkAsExtraItemCommand>
{
    public MarkAsExtraItemCommandValidator()
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

        RuleFor(x => x.Notes)
            .MaximumLength(1000)
            .When(x => !string.IsNullOrEmpty(x.Notes))
            .WithMessage("Notes cannot exceed 1000 characters.");
    }
}
