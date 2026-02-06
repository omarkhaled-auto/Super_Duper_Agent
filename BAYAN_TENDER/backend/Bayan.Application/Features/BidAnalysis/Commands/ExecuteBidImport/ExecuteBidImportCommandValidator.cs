using FluentValidation;

namespace Bayan.Application.Features.BidAnalysis.Commands.ExecuteBidImport;

/// <summary>
/// Validator for ExecuteBidImportCommand.
/// </summary>
public class ExecuteBidImportCommandValidator : AbstractValidator<ExecuteBidImportCommand>
{
    public ExecuteBidImportCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.");

        RuleFor(x => x.BidSubmissionId)
            .NotEmpty().WithMessage("Bid submission ID is required.");

        RuleFor(x => x.FxRate)
            .GreaterThan(0).WithMessage("FX rate must be greater than zero.")
            .When(x => x.FxRate.HasValue);
    }
}
