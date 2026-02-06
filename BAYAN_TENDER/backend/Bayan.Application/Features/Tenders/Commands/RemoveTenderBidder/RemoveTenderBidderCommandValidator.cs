using FluentValidation;

namespace Bayan.Application.Features.Tenders.Commands.RemoveTenderBidder;

/// <summary>
/// Validator for the RemoveTenderBidderCommand.
/// </summary>
public class RemoveTenderBidderCommandValidator : AbstractValidator<RemoveTenderBidderCommand>
{
    public RemoveTenderBidderCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidderId)
            .NotEmpty()
            .WithMessage("Bidder ID is required.");
    }
}
