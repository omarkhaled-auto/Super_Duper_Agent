using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;

namespace Bayan.Application.Features.BidAnalysis.Commands.MarkAsExtraItem;

/// <summary>
/// Command to mark a bid item as an extra item (not in BOQ).
/// </summary>
public class MarkAsExtraItemCommand : IRequest<BidItemMatchDto>
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
    /// Bid pricing item ID to mark as extra.
    /// </summary>
    public Guid ItemId { get; set; }

    /// <summary>
    /// Whether to include this extra item in the total bid amount calculation.
    /// </summary>
    public bool IncludeInTotal { get; set; }

    /// <summary>
    /// Optional notes for the extra item.
    /// </summary>
    public string? Notes { get; set; }

    public MarkAsExtraItemCommand()
    {
    }

    public MarkAsExtraItemCommand(Guid tenderId, Guid bidId, Guid itemId, bool includeInTotal = false, string? notes = null)
    {
        TenderId = tenderId;
        BidId = bidId;
        ItemId = itemId;
        IncludeInTotal = includeInTotal;
        Notes = notes;
    }
}
