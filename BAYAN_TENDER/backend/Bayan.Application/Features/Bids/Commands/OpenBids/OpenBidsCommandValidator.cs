using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.OpenBids;

/// <summary>
/// Validator for the OpenBidsCommand.
/// </summary>
public class OpenBidsCommandValidator : AbstractValidator<OpenBidsCommand>
{
    private readonly IApplicationDbContext _context;

    public OpenBidsCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExists)
            .WithMessage("The specified tender does not exist.")
            .MustAsync(TenderIsInCorrectState)
            .WithMessage("Tender must be in Active status and past the submission deadline to open bids.")
            .MustAsync(TenderHasBids)
            .WithMessage("Tender has no bids to open.")
            .MustAsync(BidsNotAlreadyOpened)
            .WithMessage("Bids for this tender have already been opened. This action is irreversible.");
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> TenderIsInCorrectState(Guid tenderId, CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == tenderId, cancellationToken);

        if (tender == null)
        {
            return true; // Will be caught by TenderExists rule
        }

        // Tender must be Active and past submission deadline
        return tender.Status == TenderStatus.Active &&
               tender.SubmissionDeadline <= DateTime.UtcNow;
    }

    private async Task<bool> TenderHasBids(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.BidSubmissions
            .AnyAsync(b => b.TenderId == tenderId, cancellationToken);
    }

    private async Task<bool> BidsNotAlreadyOpened(Guid tenderId, CancellationToken cancellationToken)
    {
        // Check if any bid has status beyond Submitted
        var hasOpenedBids = await _context.BidSubmissions
            .AnyAsync(b => b.TenderId == tenderId && b.Status != BidSubmissionStatus.Submitted, cancellationToken);

        return !hasOpenedBids;
    }
}
