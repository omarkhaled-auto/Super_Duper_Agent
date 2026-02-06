using FluentValidation;

namespace Bayan.Application.Features.VendorPricing.Queries.CompareVendorRates;

/// <summary>
/// Validator for CompareVendorRatesQuery.
/// </summary>
public class CompareVendorRatesQueryValidator : AbstractValidator<CompareVendorRatesQuery>
{
    public CompareVendorRatesQueryValidator()
    {
        RuleFor(x => x.BidderIds)
            .NotEmpty()
            .WithMessage("At least one bidder ID is required.")
            .Must(ids => ids.Count >= 2)
            .WithMessage("At least 2 vendors are required for comparison.")
            .Must(ids => ids.Count <= 5)
            .WithMessage("Maximum 5 vendors can be compared at once.");

        RuleFor(x => x.MaxItems)
            .InclusiveBetween(1, 500)
            .WithMessage("MaxItems must be between 1 and 500.");
    }
}
