using FluentValidation;

namespace Bayan.Application.Features.BidAnalysis.Commands.ValidateBidImport;

/// <summary>
/// Validator for ValidateBidImportCommand.
/// </summary>
public class ValidateBidImportCommandValidator : AbstractValidator<ValidateBidImportCommand>
{
    public ValidateBidImportCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.");

        RuleFor(x => x.BidSubmissionId)
            .NotEmpty().WithMessage("Bid submission ID is required.");

        RuleFor(x => x.FormulaTolerancePercent)
            .GreaterThanOrEqualTo(0).WithMessage("Formula tolerance must be non-negative.")
            .LessThanOrEqualTo(10).WithMessage("Formula tolerance cannot exceed 10%.");

        RuleFor(x => x.OutlierThresholdPercent)
            .GreaterThan(0).WithMessage("Outlier threshold must be greater than zero.")
            .LessThanOrEqualTo(100).WithMessage("Outlier threshold cannot exceed 100%.");
    }
}
