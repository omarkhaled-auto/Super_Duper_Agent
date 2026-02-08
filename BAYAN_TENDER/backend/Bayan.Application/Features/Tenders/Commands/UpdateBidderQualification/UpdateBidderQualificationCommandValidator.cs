using FluentValidation;

namespace Bayan.Application.Features.Tenders.Commands.UpdateBidderQualification;

/// <summary>
/// Validator for UpdateBidderQualificationCommand.
/// </summary>
public class UpdateBidderQualificationCommandValidator : AbstractValidator<UpdateBidderQualificationCommand>
{
    public UpdateBidderQualificationCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty().WithMessage("Tender ID is required.");

        RuleFor(x => x.BidderId)
            .NotEmpty().WithMessage("Bidder ID is required.");

        RuleFor(x => x.QualificationStatus)
            .NotEmpty().WithMessage("Qualification status is required.")
            .Must(status => status == "Qualified" || status == "Rejected")
            .WithMessage("Qualification status must be either 'Qualified' or 'Rejected'.");
    }
}
