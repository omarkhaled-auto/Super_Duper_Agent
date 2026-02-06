using Bayan.Application.Features.Bids.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bids.Commands.SubmitBid;

/// <summary>
/// Command to finalize and submit a bid for a tender.
/// </summary>
public class SubmitBidCommand : IRequest<SubmitBidResultDto>
{
    /// <summary>
    /// ID of the tender to submit the bid for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the bidder submitting the bid.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bid validity period in days.
    /// </summary>
    public int BidValidityDays { get; set; } = 90;
}
