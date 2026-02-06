using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;

namespace Bayan.Application.Features.BidAnalysis.Commands.UpdateManualMatch;

/// <summary>
/// Command to manually match a bid item to a BOQ item.
/// </summary>
public class UpdateManualMatchCommand : IRequest<BidItemMatchDto>
{
    /// <summary>
    /// Tender ID the bid belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bid submission ID.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// Bid pricing item ID to update.
    /// </summary>
    public Guid ItemId { get; set; }

    /// <summary>
    /// BOQ item ID to match to.
    /// </summary>
    public Guid BoqItemId { get; set; }

    /// <summary>
    /// Optional notes for the manual match.
    /// </summary>
    public string? Notes { get; set; }

    public UpdateManualMatchCommand()
    {
    }

    public UpdateManualMatchCommand(Guid tenderId, Guid bidId, Guid itemId, Guid boqItemId, string? notes = null)
    {
        TenderId = tenderId;
        BidId = bidId;
        ItemId = itemId;
        BoqItemId = boqItemId;
        Notes = notes;
    }
}
