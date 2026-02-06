using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Queries;

/// <summary>
/// Query to get tender information for the bidder portal.
/// </summary>
public class GetPortalTenderInfoQuery : IRequest<PortalTenderDto>
{
    /// <summary>
    /// Tender unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder ID for access validation.
    /// </summary>
    public Guid BidderId { get; set; }
}
