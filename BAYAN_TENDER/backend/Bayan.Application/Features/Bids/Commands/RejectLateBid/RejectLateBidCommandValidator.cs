using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.RejectLateBid;

/// <summary>
/// Validator for the RejectLateBidCommand.
/// </summary>
public class RejectLateBidCommandValidator : AbstractValidator<RejectLateBidCommand>
{
    private readonly IApplicationDbContext _context;

    public RejectLateBidCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidId)
            .NotEmpty()
            .WithMessage("Bid ID is required.")
            .MustAsync(BidExists)
            .WithMessage("The specified bid does not exist.")
            .MustAsync(BidIsLate)
            .WithMessage("Only late bids can be rejected using this command.")
            .MustAsync(DecisionNotAlreadyMade)
            .WithMessage("A decision has already been made for this late bid.");

        RuleFor(x => x.Reason)
            .NotEmpty()
            .WithMessage("A reason for rejection is required.")
            .MaximumLength(1000)
            .WithMessage("Reason cannot exceed 1000 characters.");
    }

    private async Task<bool> BidExists(RejectLateBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        return await _context.BidSubmissions
            .AnyAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);
    }

    private async Task<bool> BidIsLate(RejectLateBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);

        return bid?.IsLate == true;
    }

    private async Task<bool> DecisionNotAlreadyMade(RejectLateBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);

        return bid?.LateAccepted == null;
    }
}
