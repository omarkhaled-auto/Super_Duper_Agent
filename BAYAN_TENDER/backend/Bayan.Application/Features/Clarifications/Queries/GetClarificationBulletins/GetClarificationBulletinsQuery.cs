using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Queries.GetClarificationBulletins;

/// <summary>
/// Query for retrieving all clarification bulletins for a tender.
/// </summary>
public class GetClarificationBulletinsQuery : IRequest<List<ClarificationBulletinDto>>
{
    /// <summary>
    /// ID of the tender to get bulletins for.
    /// </summary>
    public Guid TenderId { get; set; }

    public GetClarificationBulletinsQuery()
    {
    }

    public GetClarificationBulletinsQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
