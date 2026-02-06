using Bayan.Application.Common.Models;
using Bayan.Application.Features.Clients.Commands.CreateClient;
using Bayan.Application.Features.Clients.Commands.UpdateClient;
using Bayan.Application.Features.Clients.DTOs;
using Bayan.Application.Features.Clients.Queries.GetClientById;
using Bayan.Application.Features.Clients.Queries.GetClients;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing clients.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin,TenderManager")]
public class ClientsController : ControllerBase
{
    private readonly IMediator _mediator;

    public ClientsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Gets a paginated list of clients with optional search and filtering.
    /// </summary>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="search">Optional search term for filtering by name, contact person, or email.</param>
    /// <param name="isActive">Optional filter for active status.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of clients.</returns>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<ClientDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<ClientDto>>> GetClients(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] string? search = null,
        [FromQuery] bool? isActive = null,
        CancellationToken cancellationToken = default)
    {
        var query = new GetClientsQuery
        {
            Page = page,
            PageSize = pageSize,
            Search = search,
            IsActive = isActive
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<ClientDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets a client by ID.
    /// </summary>
    /// <param name="id">The client's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The client if found.</returns>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(ClientDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClientDto>> GetClient(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var query = new GetClientByIdQuery(id);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Client not found"));
        }

        return Ok(ApiResponse<ClientDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Creates a new client.
    /// </summary>
    /// <param name="dto">The client data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created client.</returns>
    [HttpPost]
    [ProducesResponseType(typeof(ClientDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<ClientDto>> CreateClient(
        [FromBody] CreateClientDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new CreateClientCommand
        {
            Name = dto.Name,
            ContactPerson = dto.ContactPerson,
            Email = dto.Email,
            Phone = dto.Phone,
            Address = dto.Address
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetClient), new { id = result.Id }, ApiResponse<ClientDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Updates an existing client.
    /// </summary>
    /// <param name="id">The client's unique identifier.</param>
    /// <param name="dto">The updated client data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated client if found.</returns>
    [HttpPut("{id:guid}")]
    [ProducesResponseType(typeof(ClientDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<ClientDto>> UpdateClient(
        Guid id,
        [FromBody] UpdateClientDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateClientCommand
        {
            Id = id,
            Name = dto.Name,
            ContactPerson = dto.ContactPerson,
            Email = dto.Email,
            Phone = dto.Phone,
            Address = dto.Address,
            IsActive = dto.IsActive
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Client not found"));
        }

        return Ok(ApiResponse<ClientDto>.SuccessResponse(result));
    }
}
