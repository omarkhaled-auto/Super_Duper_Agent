using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Clarifications;

/// <summary>
/// Query to get the bidder's own submitted questions for a tender (any status).
/// </summary>
public class GetMyQuestionsQuery : IRequest<List<PortalClarificationDto>>
{
    /// <summary>
    /// Tender unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder ID — only questions submitted by this bidder are returned.
    /// </summary>
    public Guid BidderId { get; set; }
}
