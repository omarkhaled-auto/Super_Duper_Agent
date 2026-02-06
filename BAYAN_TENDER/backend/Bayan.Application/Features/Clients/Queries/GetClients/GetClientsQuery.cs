using Bayan.Application.Common.Models;
using Bayan.Application.Features.Clients.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clients.Queries.GetClients;

/// <summary>
/// Query for retrieving a paginated list of clients.
/// </summary>
public class GetClientsQuery : IRequest<PaginatedList<ClientDto>>
{
    /// <summary>
    /// Page number (1-based).
    /// </summary>
    public int Page { get; set; } = 1;

    /// <summary>
    /// Number of items per page.
    /// </summary>
    public int PageSize { get; set; } = 10;

    /// <summary>
    /// Optional search term for filtering clients by name or contact person.
    /// </summary>
    public string? Search { get; set; }

    /// <summary>
    /// Optional filter for active status. If null, returns all clients.
    /// </summary>
    public bool? IsActive { get; set; }
}
