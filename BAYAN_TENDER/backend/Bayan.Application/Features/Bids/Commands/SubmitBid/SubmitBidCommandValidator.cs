using FluentValidation;

namespace Bayan.Application.Features.Bids.Commands.SubmitBid;

/// <summary>
/// Validator for SubmitBidCommand.
/// </summary>
public class SubmitBidCommandValidator : AbstractValidator<SubmitBidCommand>
{
    public SubmitBidCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidderId)
            .NotEmpty()
            .WithMessage("Bidder ID is required.");

        RuleFor(x => x.BidValidityDays)
            .GreaterThan(0)
            .WithMessage("Bid validity must be greater than 0 days.")
            .LessThanOrEqualTo(365)
            .WithMessage("Bid validity cannot exceed 365 days.");
    }
}
