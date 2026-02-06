using Bayan.Application.Features.Bids.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bids.Commands.DisqualifyBid;

/// <summary>
/// Command for disqualifying a bid submission.
/// </summary>
public class DisqualifyBidCommand : IRequest<DisqualifyBidResultDto>
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
    /// Reason for disqualification.
    /// </summary>
    public string Reason { get; set; } = string.Empty;
}
