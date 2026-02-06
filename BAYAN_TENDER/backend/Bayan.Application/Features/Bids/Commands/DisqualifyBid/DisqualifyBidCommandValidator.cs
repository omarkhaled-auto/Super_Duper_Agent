using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.DisqualifyBid;

/// <summary>
/// Validator for the DisqualifyBidCommand.
/// </summary>
public class DisqualifyBidCommandValidator : AbstractValidator<DisqualifyBidCommand>
{
    private readonly IApplicationDbContext _context;

    public DisqualifyBidCommandValidator(IApplicationDbContext context)
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
            .MustAsync(BidNotAlreadyDisqualified)
            .WithMessage("This bid has already been disqualified.")
            .MustAsync(BidsHaveBeenOpened)
            .WithMessage("Bids must be opened before disqualification.");

        RuleFor(x => x.Reason)
            .NotEmpty()
            .WithMessage("A reason for disqualification is required.")
            .MaximumLength(2000)
            .WithMessage("Reason cannot exceed 2000 characters.");
    }

    private async Task<bool> BidExists(DisqualifyBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        return await _context.BidSubmissions
            .AnyAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);
    }

    private async Task<bool> BidNotAlreadyDisqualified(DisqualifyBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);

        return bid?.Status != BidSubmissionStatus.Disqualified;
    }

    private async Task<bool> BidsHaveBeenOpened(DisqualifyBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);

        if (bid == null)
        {
            return true; // Will be caught by BidExists rule
        }

        // Can only disqualify bids that have been opened or imported
        return bid.Status == BidSubmissionStatus.Opened ||
               bid.Status == BidSubmissionStatus.Imported;
    }
}
