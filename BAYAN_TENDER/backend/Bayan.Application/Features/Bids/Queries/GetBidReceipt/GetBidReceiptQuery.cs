using Bayan.Application.Features.Bids.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bids.Queries.GetBidReceipt;

/// <summary>
/// Query to get a bid receipt.
/// </summary>
public class GetBidReceiptQuery : IRequest<BidReceiptDto?>
{
    /// <summary>
    /// ID of the bid submission.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// ID of the bidder (for authorization).
    /// </summary>
    public Guid BidderId { get; set; }

    public GetBidReceiptQuery(Guid bidId, Guid bidderId)
    {
        BidId = bidId;
        BidderId = bidderId;
    }
}
