using FluentValidation;

namespace Bayan.Application.Features.BidAnalysis.Commands.ParseBidFile;

/// <summary>
/// Validator for ParseBidFileCommand.
/// </summary>
public class ParseBidFileCommandValidator : AbstractValidator<ParseBidFileCommand>
{
    public ParseBidFileCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidId)
            .NotEmpty()
            .WithMessage("Bid ID is required.");

        RuleFor(x => x.PreviewRowCount)
            .GreaterThan(0)
            .WithMessage("Preview row count must be greater than 0.")
            .LessThanOrEqualTo(100)
            .WithMessage("Preview row count cannot exceed 100.");
    }
}
