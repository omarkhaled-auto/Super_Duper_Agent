using MediatR;

namespace Bayan.Application.Features.Tenders.Commands.RemoveTenderBidder;

/// <summary>
/// Command for removing a bidder from a tender.
/// </summary>
public class RemoveTenderBidderCommand : IRequest<bool>
{
    /// <summary>
    /// The tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The bidder ID to remove.
    /// </summary>
    public Guid BidderId { get; set; }

    public RemoveTenderBidderCommand(Guid tenderId, Guid bidderId)
    {
        TenderId = tenderId;
        BidderId = bidderId;
    }
}
