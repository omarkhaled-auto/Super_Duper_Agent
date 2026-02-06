using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Documents;

/// <summary>
/// Query to get addenda with acknowledgment status for the current bidder.
/// </summary>
public class GetPortalAddendaQuery : IRequest<List<PortalAddendumDto>>
{
    /// <summary>
    /// Tender unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder ID for access validation and acknowledgment status.
    /// </summary>
    public Guid BidderId { get; set; }
}
