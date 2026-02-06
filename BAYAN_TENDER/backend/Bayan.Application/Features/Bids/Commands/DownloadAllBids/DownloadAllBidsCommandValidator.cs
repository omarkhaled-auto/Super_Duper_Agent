using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.DownloadAllBids;

/// <summary>
/// Validator for the DownloadAllBidsCommand.
/// </summary>
public class DownloadAllBidsCommandValidator : AbstractValidator<DownloadAllBidsCommand>
{
    private readonly IApplicationDbContext _context;

    public DownloadAllBidsCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExists)
            .WithMessage("The specified tender does not exist.")
            .MustAsync(TenderHasBids)
            .WithMessage("Tender has no bids to download.")
            .MustAsync(BidsHaveBeenOpened)
            .WithMessage("Bids must be opened before downloading.");
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> TenderHasBids(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.BidSubmissions
            .AnyAsync(b => b.TenderId == tenderId, cancellationToken);
    }

    private async Task<bool> BidsHaveBeenOpened(Guid tenderId, CancellationToken cancellationToken)
    {
        // Check if tender is in Evaluation status or has opened bids
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == tenderId, cancellationToken);

        if (tender == null)
        {
            return true; // Will be caught by TenderExists rule
        }

        // Allow download if tender is in Evaluation or Awarded status
        // or if any bid has been opened
        if (tender.Status == TenderStatus.Evaluation || tender.Status == TenderStatus.Awarded)
        {
            return true;
        }

        return await _context.BidSubmissions
            .AnyAsync(b => b.TenderId == tenderId &&
                         (b.Status == BidSubmissionStatus.Opened ||
                          b.Status == BidSubmissionStatus.Imported ||
                          b.Status == BidSubmissionStatus.Disqualified),
                     cancellationToken);
    }
}
