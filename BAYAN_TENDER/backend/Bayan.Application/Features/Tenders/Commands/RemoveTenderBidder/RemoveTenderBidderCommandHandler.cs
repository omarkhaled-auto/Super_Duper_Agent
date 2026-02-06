using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.RemoveTenderBidder;

/// <summary>
/// Handler for the RemoveTenderBidderCommand.
/// </summary>
public class RemoveTenderBidderCommandHandler : IRequestHandler<RemoveTenderBidderCommand, bool>
{
    private readonly IApplicationDbContext _context;

    public RemoveTenderBidderCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<bool> Handle(
        RemoveTenderBidderCommand request,
        CancellationToken cancellationToken)
    {
        var tenderBidder = await _context.TenderBidders
            .FirstOrDefaultAsync(
                tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId,
                cancellationToken);

        if (tenderBidder == null)
        {
            return false;
        }

        _context.TenderBidders.Remove(tenderBidder);
        await _context.SaveChangesAsync(cancellationToken);

        return true;
    }
}
