using Bayan.Application.Features.Bids.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bids.Queries.GetBidDetails;

/// <summary>
/// Query for retrieving full details of a specific bid.
/// </summary>
public class GetBidDetailsQuery : IRequest<BidDetailDto?>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; }

    /// <summary>
    /// ID of the bid submission.
    /// </summary>
    public Guid BidId { get; }

    public GetBidDetailsQuery(Guid tenderId, Guid bidId)
    {
        TenderId = tenderId;
        BidId = bidId;
    }
}
