using Bayan.Application.Features.Addenda.DTOs;
using MediatR;

namespace Bayan.Application.Features.Addenda.Commands.IssueAddendum;

/// <summary>
/// Command for issuing an addendum (publishing it and sending notifications to bidders).
/// </summary>
public class IssueAddendumCommand : IRequest<AddendumDto>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the addendum to issue.
    /// </summary>
    public Guid AddendumId { get; set; }

    public IssueAddendumCommand(Guid tenderId, Guid addendumId)
    {
        TenderId = tenderId;
        AddendumId = addendumId;
    }
}
