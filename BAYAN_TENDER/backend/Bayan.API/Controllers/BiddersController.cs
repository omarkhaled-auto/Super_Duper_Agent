using Bayan.Application.Common.Models;
using Bayan.Application.Features.Bidders.Commands.CreateBidder;
using Bayan.Application.Features.Bidders.Commands.UpdateBidder;
using Bayan.Application.Features.Bidders.DTOs;
using Bayan.Application.Features.Bidders.Queries.GetBidderById;
using Bayan.Application.Features.Bidders.Queries.GetBidders;
using Bayan.API.Authorization;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing bidders.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
public class BiddersController : ControllerBase
{
    private readonly IMediator _mediator;

    public BiddersController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Gets a paginated list of bidders with optional search and filtering.
    /// </summary>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="search">Optional search term for filtering by company name, contact person, email, or CR number.</param>
    /// <param name="tradeSpecialization">Optional filter by trade specialization.</param>
    /// <param name="prequalificationStatus">Optional filter by prequalification status.</param>
    /// <param name="isActive">Optional filter for active status.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of bidders.</returns>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<BidderDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<BidderDto>>> GetBidders(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] string? search = null,
        [FromQuery] string? tradeSpecialization = null,
        [FromQuery] PrequalificationStatus? prequalificationStatus = null,
        [FromQuery] bool? isActive = null,
        CancellationToken cancellationToken = default)
    {
        var query = new GetBiddersQuery
        {
            Page = page,
            PageSize = pageSize,
            Search = search,
            TradeSpecialization = tradeSpecialization,
            PrequalificationStatus = prequalificationStatus,
            IsActive = isActive
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<BidderDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets a bidder by ID with full details.
    /// </summary>
    /// <param name="id">The bidder's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The bidder if found.</returns>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(BidderDetailDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BidderDetailDto>> GetBidder(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var query = new GetBidderByIdQuery(id);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Bidder not found"));
        }

        return Ok(ApiResponse<BidderDetailDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Creates a new bidder.
    /// </summary>
    /// <param name="dto">The bidder data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created bidder.</returns>
    [HttpPost]
    [ProducesResponseType(typeof(BidderDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<BidderDto>> CreateBidder(
        [FromBody] CreateBidderDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new CreateBidderCommand
        {
            CompanyName = dto.CompanyName,
            CRNumber = dto.CRNumber,
            LicenseNumber = dto.LicenseNumber,
            ContactPerson = dto.ContactPerson,
            Email = dto.Email,
            Phone = dto.Phone,
            TradeSpecialization = dto.TradeSpecialization
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetBidder), new { id = result.Id }, ApiResponse<BidderDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Updates an existing bidder.
    /// </summary>
    /// <param name="id">The bidder's unique identifier.</param>
    /// <param name="dto">The updated bidder data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated bidder if found.</returns>
    [HttpPut("{id:guid}")]
    [ProducesResponseType(typeof(BidderDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<BidderDto>> UpdateBidder(
        Guid id,
        [FromBody] UpdateBidderDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateBidderCommand
        {
            Id = id,
            CompanyName = dto.CompanyName,
            CRNumber = dto.CRNumber,
            LicenseNumber = dto.LicenseNumber,
            ContactPerson = dto.ContactPerson,
            Email = dto.Email,
            Phone = dto.Phone,
            TradeSpecialization = dto.TradeSpecialization,
            PrequalificationStatus = dto.PrequalificationStatus,
            IsActive = dto.IsActive
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Bidder not found"));
        }

        return Ok(ApiResponse<BidderDto>.SuccessResponse(result));
    }
}
