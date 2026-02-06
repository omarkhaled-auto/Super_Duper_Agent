using Bayan.Application.Features.Tenders.DTOs;
using MediatR;

namespace Bayan.Application.Features.Tenders.Commands.InviteBidders;

/// <summary>
/// Command for inviting bidders to a tender.
/// </summary>
public class InviteBiddersCommand : IRequest<InviteBiddersResult>
{
    /// <summary>
    /// The tender ID to invite bidders to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// List of bidder IDs to invite.
    /// </summary>
    public List<Guid> BidderIds { get; set; } = new();
}

/// <summary>
/// Result of the invite bidders operation.
/// </summary>
public class InviteBiddersResult
{
    /// <summary>
    /// Number of bidders successfully invited.
    /// </summary>
    public int InvitedCount { get; set; }

    /// <summary>
    /// Number of bidders that were already invited.
    /// </summary>
    public int AlreadyInvitedCount { get; set; }

    /// <summary>
    /// List of tender bidder relationships created.
    /// </summary>
    public List<TenderBidderDto> InvitedBidders { get; set; } = new();
}
