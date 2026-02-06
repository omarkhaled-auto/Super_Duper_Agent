using MediatR;

namespace Bayan.Application.Features.Portal.Documents;

/// <summary>
/// Command to acknowledge an addendum.
/// </summary>
public class AcknowledgeAddendumCommand : IRequest<bool>
{
    /// <summary>
    /// Tender unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Addendum unique identifier.
    /// </summary>
    public Guid AddendumId { get; set; }

    /// <summary>
    /// Bidder ID acknowledging the addendum.
    /// </summary>
    public Guid BidderId { get; set; }
}
