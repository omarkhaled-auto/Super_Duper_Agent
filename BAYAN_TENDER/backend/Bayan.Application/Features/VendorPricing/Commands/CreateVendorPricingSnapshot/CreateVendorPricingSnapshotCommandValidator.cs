using FluentValidation;

namespace Bayan.Application.Features.VendorPricing.Commands.CreateVendorPricingSnapshot;

/// <summary>
/// Validator for CreateVendorPricingSnapshotCommand.
/// </summary>
public class CreateVendorPricingSnapshotCommandValidator : AbstractValidator<CreateVendorPricingSnapshotCommand>
{
    public CreateVendorPricingSnapshotCommandValidator()
    {
        RuleFor(x => x.BidSubmissionId)
            .NotEmpty()
            .WithMessage("Bid submission ID is required.");
    }
}
