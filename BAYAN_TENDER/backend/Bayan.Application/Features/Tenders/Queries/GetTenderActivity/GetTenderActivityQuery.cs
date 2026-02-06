using Bayan.Application.Features.Tenders.DTOs;
using MediatR;

namespace Bayan.Application.Features.Tenders.Queries.GetTenderActivity;

/// <summary>
/// Query for retrieving recent activity for a tender.
/// </summary>
public class GetTenderActivityQuery : IRequest<List<TenderActivityDto>>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    /// <summary>
    /// Maximum number of activities to return.
    /// </summary>
    public int Limit { get; set; } = 50;

    public GetTenderActivityQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
