using MediatR;

namespace Bayan.Application.Features.Addenda.Commands.AcknowledgeAddendum;

/// <summary>
/// Command for a bidder to acknowledge receipt of an addendum.
/// </summary>
public class AcknowledgeAddendumCommand : IRequest<bool>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the addendum to acknowledge.
    /// </summary>
    public Guid AddendumId { get; set; }

    /// <summary>
    /// ID of the bidder acknowledging the addendum.
    /// </summary>
    public Guid BidderId { get; set; }

    public AcknowledgeAddendumCommand(Guid tenderId, Guid addendumId, Guid bidderId)
    {
        TenderId = tenderId;
        AddendumId = addendumId;
        BidderId = bidderId;
    }
}
