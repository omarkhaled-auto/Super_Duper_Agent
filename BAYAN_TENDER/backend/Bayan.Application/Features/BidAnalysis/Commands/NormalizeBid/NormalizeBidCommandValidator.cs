using FluentValidation;

namespace Bayan.Application.Features.BidAnalysis.Commands.NormalizeBid;

/// <summary>
/// Validator for NormalizeBidCommand.
/// </summary>
public class NormalizeBidCommandValidator : AbstractValidator<NormalizeBidCommand>
{
    public NormalizeBidCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.");

        RuleFor(x => x.BidSubmissionId)
            .NotEmpty().WithMessage("Bid submission ID is required.");

        RuleFor(x => x.FxRate)
            .GreaterThan(0).WithMessage("FX rate must be greater than zero.")
            .When(x => x.FxRate.HasValue);

        RuleFor(x => x.FxRateSource)
            .MaximumLength(100).WithMessage("FX rate source must not exceed 100 characters.")
            .When(x => !string.IsNullOrEmpty(x.FxRateSource));
    }
}
