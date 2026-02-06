using Bayan.Application.Features.Tenders.DTOs;
using MediatR;

namespace Bayan.Application.Features.Tenders.Queries.GetTenderById;

/// <summary>
/// Query for retrieving a tender by ID with full details including bidders and criteria.
/// </summary>
public class GetTenderByIdQuery : IRequest<TenderDetailDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid Id { get; }

    public GetTenderByIdQuery(Guid id)
    {
        Id = id;
    }
}
