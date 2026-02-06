using FluentValidation;

namespace Bayan.Application.Features.Portal.Clarifications;

/// <summary>
/// Validator for SubmitBidderQuestionCommand.
/// </summary>
public class SubmitBidderQuestionCommandValidator : AbstractValidator<SubmitBidderQuestionCommand>
{
    public SubmitBidderQuestionCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.");

        RuleFor(x => x.BidderId)
            .NotEmpty().WithMessage("Bidder ID is required.");

        RuleFor(x => x.Subject)
            .NotEmpty().WithMessage("Subject is required.")
            .MaximumLength(200).WithMessage("Subject must not exceed 200 characters.");

        RuleFor(x => x.Question)
            .NotEmpty().WithMessage("Question is required.")
            .MaximumLength(4000).WithMessage("Question must not exceed 4000 characters.");

        RuleFor(x => x.RelatedBoqSection)
            .MaximumLength(100).WithMessage("Related BOQ section must not exceed 100 characters.")
            .When(x => !string.IsNullOrEmpty(x.RelatedBoqSection));
    }
}
