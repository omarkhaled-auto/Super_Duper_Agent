using Bayan.Application.Features.Addenda.DTOs;
using MediatR;

namespace Bayan.Application.Features.Addenda.Queries.GetAddenda;

/// <summary>
/// Query for retrieving all addenda for a tender.
/// </summary>
public class GetAddendaQuery : IRequest<List<AddendumDto>>
{
    /// <summary>
    /// ID of the tender to get addenda for.
    /// </summary>
    public Guid TenderId { get; set; }

    public GetAddendaQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
