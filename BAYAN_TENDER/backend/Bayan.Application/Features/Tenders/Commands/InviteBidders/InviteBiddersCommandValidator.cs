using FluentValidation;

namespace Bayan.Application.Features.Tenders.Commands.InviteBidders;

/// <summary>
/// Validator for the InviteBiddersCommand.
/// </summary>
public class InviteBiddersCommandValidator : AbstractValidator<InviteBiddersCommand>
{
    public InviteBiddersCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidderIds)
            .NotEmpty()
            .WithMessage("At least one bidder ID is required.")
            .Must(ids => ids.All(id => id != Guid.Empty))
            .WithMessage("All bidder IDs must be valid.");
    }
}
