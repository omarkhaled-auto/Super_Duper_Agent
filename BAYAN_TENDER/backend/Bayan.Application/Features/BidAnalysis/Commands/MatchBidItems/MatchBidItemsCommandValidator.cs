using FluentValidation;

namespace Bayan.Application.Features.BidAnalysis.Commands.MatchBidItems;

/// <summary>
/// Validator for MatchBidItemsCommand.
/// </summary>
public class MatchBidItemsCommandValidator : AbstractValidator<MatchBidItemsCommand>
{
    public MatchBidItemsCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidId)
            .NotEmpty()
            .WithMessage("Bid ID is required.");

        RuleFor(x => x.Items)
            .NotNull()
            .WithMessage("Items list is required.")
            .Must(x => x.Count > 0)
            .WithMessage("At least one item is required for matching.");

        RuleFor(x => x.FuzzyMatchThreshold)
            .InclusiveBetween(0, 100)
            .WithMessage("Fuzzy match threshold must be between 0 and 100.");

        RuleFor(x => x.AlternativeMatchCount)
            .InclusiveBetween(0, 10)
            .WithMessage("Alternative match count must be between 0 and 10.");
    }
}
