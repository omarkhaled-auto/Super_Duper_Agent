using Bayan.Application.Features.Clients.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clients.Queries.GetClientById;

/// <summary>
/// Query for retrieving a single client by ID.
/// </summary>
public class GetClientByIdQuery : IRequest<ClientDto?>
{
    /// <summary>
    /// The unique identifier of the client to retrieve.
    /// </summary>
    public Guid Id { get; set; }

    public GetClientByIdQuery(Guid id)
    {
        Id = id;
    }
}
