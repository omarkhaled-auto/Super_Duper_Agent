using Bayan.Application.Features.Addenda.DTOs;
using MediatR;

namespace Bayan.Application.Features.Addenda.Queries.GetAddendumById;

/// <summary>
/// Query for retrieving an addendum by ID with full details.
/// </summary>
public class GetAddendumByIdQuery : IRequest<AddendumDetailDto?>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the addendum to retrieve.
    /// </summary>
    public Guid AddendumId { get; set; }

    public GetAddendumByIdQuery(Guid tenderId, Guid addendumId)
    {
        TenderId = tenderId;
        AddendumId = addendumId;
    }
}
