using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Queries.GetClarificationById;

/// <summary>
/// Query for retrieving a clarification by ID with full details.
/// </summary>
public class GetClarificationByIdQuery : IRequest<ClarificationDetailDto?>
{
    /// <summary>
    /// ID of the tender the clarification belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the clarification to retrieve.
    /// </summary>
    public Guid ClarificationId { get; set; }

    public GetClarificationByIdQuery()
    {
    }

    public GetClarificationByIdQuery(Guid tenderId, Guid clarificationId)
    {
        TenderId = tenderId;
        ClarificationId = clarificationId;
    }
}
