using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.AcceptLateBid;

/// <summary>
/// Validator for the AcceptLateBidCommand.
/// </summary>
public class AcceptLateBidCommandValidator : AbstractValidator<AcceptLateBidCommand>
{
    private readonly IApplicationDbContext _context;

    public AcceptLateBidCommandValidator(IApplicationDbContext context)
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
            .WithMessage("Only late bids can be accepted using this command.")
            .MustAsync(DecisionNotAlreadyMade)
            .WithMessage("A decision has already been made for this late bid.");
    }

    private async Task<bool> BidExists(AcceptLateBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        return await _context.BidSubmissions
            .AnyAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);
    }

    private async Task<bool> BidIsLate(AcceptLateBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);

        return bid?.IsLate == true;
    }

    private async Task<bool> DecisionNotAlreadyMade(AcceptLateBidCommand command, Guid bidId, CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == bidId && b.TenderId == command.TenderId, cancellationToken);

        return bid?.LateAccepted == null;
    }
}
