using Bayan.Application.Features.Bids.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bids.Commands.RejectLateBid;

/// <summary>
/// Command for rejecting a late bid submission.
/// Sends notification to the bidder.
/// </summary>
public class RejectLateBidCommand : IRequest<LateBidDecisionDto>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the bid submission.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// Reason for rejecting the late bid.
    /// </summary>
    public string Reason { get; set; } = string.Empty;
}
