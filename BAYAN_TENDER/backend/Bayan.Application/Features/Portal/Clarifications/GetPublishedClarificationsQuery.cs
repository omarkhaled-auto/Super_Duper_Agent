using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Clarifications;

/// <summary>
/// Query to get published clarifications (Q&A) for a tender.
/// </summary>
public class GetPublishedClarificationsQuery : IRequest<List<PortalClarificationDto>>
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
