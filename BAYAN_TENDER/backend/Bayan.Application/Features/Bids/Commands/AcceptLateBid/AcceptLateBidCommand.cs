using Bayan.Application.Features.Bids.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bids.Commands.AcceptLateBid;

/// <summary>
/// Command for accepting a late bid submission.
/// </summary>
public class AcceptLateBidCommand : IRequest<LateBidDecisionDto>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; }

    /// <summary>
    /// ID of the bid submission.
    /// </summary>
    public Guid BidId { get; }

    public AcceptLateBidCommand(Guid tenderId, Guid bidId)
    {
        TenderId = tenderId;
        BidId = bidId;
    }
}
