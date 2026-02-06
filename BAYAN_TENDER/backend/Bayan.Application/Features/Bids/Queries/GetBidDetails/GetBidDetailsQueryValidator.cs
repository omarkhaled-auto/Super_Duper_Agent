using FluentValidation;

namespace Bayan.Application.Features.Bids.Queries.GetBidDetails;

/// <summary>
/// Validator for the GetBidDetailsQuery.
/// </summary>
public class GetBidDetailsQueryValidator : AbstractValidator<GetBidDetailsQuery>
{
    public GetBidDetailsQueryValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidId)
            .NotEmpty()
            .WithMessage("Bid ID is required.");
    }
}
