using Bayan.Application.Common.Models;
using Bayan.Application.Features.Addenda.Commands.AcknowledgeAddendum;
using Bayan.Application.Features.Addenda.Commands.CreateAddendum;
using Bayan.Application.Features.Addenda.Commands.IssueAddendum;
using Bayan.Application.Features.Addenda.DTOs;
using Bayan.Application.Features.Addenda.Queries.GetAddenda;
using Bayan.Application.Features.Addenda.Queries.GetAddendumById;
using Bayan.Application.Features.Tenders.Commands.CancelTender;
using Bayan.Application.Features.Tenders.Commands.CloseTender;
using Bayan.Application.Features.Tenders.Commands.CreateTender;
using Bayan.Application.Features.Tenders.Commands.InviteBidders;
using Bayan.Application.Features.Tenders.Commands.PublishTender;
using Bayan.Application.Features.Tenders.Commands.RemoveTenderBidder;
using Bayan.Application.Features.Tenders.Commands.UpdateBidderQualification;
using Bayan.Application.Features.Tenders.Commands.SetPricingLevel;
using Bayan.Application.Features.Tenders.Commands.UpdateTender;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Application.Features.Tenders.Queries.ExportTenders;
using Bayan.Application.Features.Tenders.Queries.GetNextTenderReference;
using Bayan.Application.Features.Tenders.Queries.GetTenderActivity;
using Bayan.Application.Features.Tenders.Queries.GetTenderBidders;
using Bayan.Application.Features.Tenders.Queries.GetTenderById;
using Bayan.Application.Features.Tenders.Queries.GetTenders;
using Bayan.API.Authorization;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing tenders.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = BayanRoles.InternalUsers)]
public class TendersController : ControllerBase
{
    private readonly IMediator _mediator;

    public TendersController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Gets a paginated list of tenders with optional filtering and search.
    /// </summary>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="status">Optional filter by tender status.</param>
    /// <param name="clientId">Optional filter by client ID.</param>
    /// <param name="dateFrom">Optional filter by start date.</param>
    /// <param name="dateTo">Optional filter by end date.</param>
    /// <param name="search">Optional search term for title or reference.</param>
    /// <param name="tenderType">Optional filter by tender type.</param>
    /// <param name="sortBy">Sort field (default: CreatedAt).</param>
    /// <param name="sortDescending">Sort direction (default: descending).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of tenders.</returns>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<TenderListDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<TenderListDto>>> GetTenders(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] TenderStatus? status = null,
        [FromQuery] Guid? clientId = null,
        [FromQuery] DateTime? dateFrom = null,
        [FromQuery] DateTime? dateTo = null,
        [FromQuery] string? search = null,
        [FromQuery] TenderType? tenderType = null,
        [FromQuery] string sortBy = "CreatedAt",
        [FromQuery] bool sortDescending = true,
        CancellationToken cancellationToken = default)
    {
        var query = new GetTendersQuery
        {
            Page = page,
            PageSize = pageSize,
            Status = status,
            ClientId = clientId,
            DateFrom = dateFrom,
            DateTo = dateTo,
            Search = search,
            TenderType = tenderType,
            SortBy = sortBy,
            SortDescending = sortDescending
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<TenderListDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Exports all tenders to an Excel file.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>An Excel file containing all tenders.</returns>
    [HttpGet("export")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    public async Task<IActionResult> ExportTenders(CancellationToken cancellationToken = default)
    {
        var query = new ExportTendersQuery();
        var result = await _mediator.Send(query, cancellationToken);
        return File(result.FileContent, result.ContentType, result.FileName);
    }

    /// <summary>
    /// Gets a tender by ID with full details including bidders and evaluation criteria.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The tender details if found.</returns>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(TenderDetailDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<TenderDetailDto>> GetTender(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var query = new GetTenderByIdQuery(id);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Tender not found"));
        }

        return Ok(ApiResponse<TenderDetailDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the next available tender reference number.
    /// Format: TNR-{YEAR}-{4-digit-sequence}
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The next tender reference number.</returns>
    [HttpGet("next-reference")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(string), StatusCodes.Status200OK)]
    public async Task<ActionResult<string>> GetNextReference(
        CancellationToken cancellationToken = default)
    {
        var query = new GetNextTenderReferenceQuery();
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<string>.SuccessResponse(result));
    }

    /// <summary>
    /// Creates a new tender.
    /// </summary>
    /// <param name="dto">The tender data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created tender.</returns>
    [HttpPost]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(TenderDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<TenderDto>> CreateTender(
        [FromBody] CreateTenderDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new CreateTenderCommand
        {
            Title = dto.Title,
            Description = dto.Description,
            ClientId = dto.ClientId,
            TenderType = dto.TenderType,
            BaseCurrency = dto.BaseCurrency,
            EstimatedValue = dto.EstimatedValue,
            BidValidityDays = dto.BidValidityDays,
            IssueDate = dto.IssueDate,
            ClarificationDeadline = dto.ClarificationDeadline,
            SubmissionDeadline = dto.SubmissionDeadline,
            OpeningDate = dto.OpeningDate,
            TechnicalWeight = dto.TechnicalWeight,
            CommercialWeight = dto.CommercialWeight,
            PricingLevel = dto.PricingLevel,
            EvaluationCriteria = dto.EvaluationCriteria
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetTender), new { id = result.Id }, ApiResponse<TenderDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Updates an existing tender.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="dto">The updated tender data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated tender if found.</returns>
    [HttpPut("{id:guid}")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(TenderDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<TenderDto>> UpdateTender(
        Guid id,
        [FromBody] UpdateTenderDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateTenderCommand
        {
            Id = id,
            Title = dto.Title,
            Description = dto.Description,
            ClientId = dto.ClientId,
            TenderType = dto.TenderType,
            BaseCurrency = dto.BaseCurrency,
            EstimatedValue = dto.EstimatedValue,
            BidValidityDays = dto.BidValidityDays,
            IssueDate = dto.IssueDate,
            ClarificationDeadline = dto.ClarificationDeadline,
            SubmissionDeadline = dto.SubmissionDeadline,
            OpeningDate = dto.OpeningDate,
            TechnicalWeight = dto.TechnicalWeight,
            CommercialWeight = dto.CommercialWeight,
            PricingLevel = dto.PricingLevel,
            EvaluationCriteria = dto.EvaluationCriteria
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Tender not found"));
        }

        return Ok(ApiResponse<TenderDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Sets the pricing level for a tender's BOQ.
    /// Cannot be changed after bids have been submitted.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="request">The pricing level to set.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result with priceable node count.</returns>
    [HttpPut("{id:guid}/pricing-level")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(SetPricingLevelResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<SetPricingLevelResult>> SetPricingLevel(
        Guid id,
        [FromBody] SetPricingLevelRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var command = new SetPricingLevelCommand
            {
                TenderId = id,
                PricingLevel = request.PricingLevel
            };

            var result = await _mediator.Send(command, cancellationToken);

            if (result == null)
            {
                return NotFound(ApiResponse<object>.FailureResponse("Tender not found"));
            }

            return Ok(ApiResponse<SetPricingLevelResult>.SuccessResponse(result));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Publishes a tender, transitioning it from Draft to Active status.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The published tender if found.</returns>
    [HttpPost("{id:guid}/publish")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(TenderDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<TenderDto>> PublishTender(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var command = new PublishTenderCommand(id);
        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Tender not found"));
        }

        return Ok(ApiResponse<TenderDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Cancels a tender.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="request">Optional cancellation reason.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The cancelled tender if found.</returns>
    [HttpPost("{id:guid}/cancel")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(TenderDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<TenderDto>> CancelTender(
        Guid id,
        [FromBody] CancelTenderRequest? request = null,
        CancellationToken cancellationToken = default)
    {
        var command = new CancelTenderCommand(id)
        {
            Reason = request?.Reason
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Tender not found"));
        }

        return Ok(ApiResponse<TenderDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Closes a tender (transitions from Active to Evaluation).
    /// Stops accepting bids and begins the evaluation phase.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The closed tender if found.</returns>
    [HttpPost("{id:guid}/close")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(TenderDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<TenderDto>> CloseTender(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var command = new CloseTenderCommand(id);

        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Tender not found"));
        }

        return Ok(ApiResponse<TenderDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets recent activity for a tender.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="limit">Maximum number of activities to return (default: 50).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of recent activities for the tender.</returns>
    [HttpGet("{id:guid}/activity")]
    [ProducesResponseType(typeof(List<TenderActivityDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<List<TenderActivityDto>>> GetTenderActivity(
        Guid id,
        [FromQuery] int limit = 50,
        CancellationToken cancellationToken = default)
    {
        // First check if tender exists
        var tenderQuery = new GetTenderByIdQuery(id);
        var tender = await _mediator.Send(tenderQuery, cancellationToken);

        if (tender == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Tender not found"));
        }

        var query = new GetTenderActivityQuery(id) { Limit = limit };
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<List<TenderActivityDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the list of bidders invited to a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of tender bidders.</returns>
    [HttpGet("{tenderId:guid}/bidders")]
    [ProducesResponseType(typeof(PaginatedList<TenderBidderDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<TenderBidderDto>>> GetTenderBidders(
        Guid tenderId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        CancellationToken cancellationToken = default)
    {
        var query = new GetTenderBiddersQuery(tenderId, page, pageSize);
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<TenderBidderDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Invites bidders to a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidderIds">List of bidder IDs to invite.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result of the invitation operation.</returns>
    [HttpPost("{tenderId:guid}/invite")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(InviteBiddersResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<InviteBiddersResult>> InviteBidders(
        Guid tenderId,
        [FromBody] List<Guid> bidderIds,
        CancellationToken cancellationToken = default)
    {
        var command = new InviteBiddersCommand
        {
            TenderId = tenderId,
            BidderIds = bidderIds
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<InviteBiddersResult>.SuccessResponse(result));
    }

    /// <summary>
    /// Removes a bidder from a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidderId">The bidder's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>No content if successful, NotFound otherwise.</returns>
    [HttpDelete("{tenderId:guid}/bidders/{bidderId:guid}")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> RemoveTenderBidder(
        Guid tenderId,
        Guid bidderId,
        CancellationToken cancellationToken = default)
    {
        var command = new RemoveTenderBidderCommand(tenderId, bidderId);
        var result = await _mediator.Send(command, cancellationToken);

        if (!result)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Tender bidder not found"));
        }

        return NoContent();
    }

    /// <summary>
    /// Updates the qualification status of a bidder for a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidderId">The bidder's unique identifier.</param>
    /// <param name="request">The qualification update request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Success status.</returns>
    [HttpPut("{tenderId:guid}/bidders/{bidderId:guid}/qualification")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateBidderQualification(
        Guid tenderId,
        Guid bidderId,
        [FromBody] UpdateBidderQualificationRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateBidderQualificationCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            QualificationStatus = request.QualificationStatus,
            Reason = request.Reason
        };

        try
        {
            await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<object>.SuccessResponse(new { message = "Bidder qualification status updated successfully." }));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #region Addenda Endpoints

    /// <summary>
    /// Gets all addenda for a tender.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of addenda for the tender.</returns>
    [HttpGet("{id:guid}/addenda")]
    [ProducesResponseType(typeof(List<AddendumDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<List<AddendumDto>>> GetAddenda(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        // First check if tender exists
        var tenderQuery = new GetTenderByIdQuery(id);
        var tender = await _mediator.Send(tenderQuery, cancellationToken);

        if (tender == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Tender not found"));
        }

        var query = new GetAddendaQuery(id);
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<List<AddendumDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets an addendum by ID with full details including acknowledgments.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="addendumId">The addendum's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The addendum details if found.</returns>
    [HttpGet("{id:guid}/addenda/{addendumId:guid}")]
    [ProducesResponseType(typeof(AddendumDetailDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<AddendumDetailDto>> GetAddendum(
        Guid id,
        Guid addendumId,
        CancellationToken cancellationToken = default)
    {
        var query = new GetAddendumByIdQuery(id, addendumId);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Addendum not found"));
        }

        return Ok(ApiResponse<AddendumDetailDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Creates a new addendum for a tender.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="dto">The addendum data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created addendum.</returns>
    [HttpPost("{id:guid}/addenda")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(AddendumDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<AddendumDto>> CreateAddendum(
        Guid id,
        [FromBody] CreateAddendumDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new CreateAddendumCommand
        {
            TenderId = id,
            Summary = dto.Summary,
            ExtendsDeadline = dto.ExtendsDeadline,
            NewDeadline = dto.NewDeadline
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetAddendum), new { id, addendumId = result.Id }, ApiResponse<AddendumDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Issues an addendum, sending notifications to all qualified bidders.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="addendumId">The addendum's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The issued addendum.</returns>
    [HttpPost("{id:guid}/addenda/{addendumId:guid}/issue")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(AddendumDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<AddendumDto>> IssueAddendum(
        Guid id,
        Guid addendumId,
        CancellationToken cancellationToken = default)
    {
        var command = new IssueAddendumCommand(id, addendumId);
        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<AddendumDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Acknowledges receipt of an addendum by a bidder.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="addendumId">The addendum's unique identifier.</param>
    /// <param name="request">The acknowledgment request containing the bidder ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Success status.</returns>
    [HttpPost("{id:guid}/addenda/{addendumId:guid}/acknowledge")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> AcknowledgeAddendum(
        Guid id,
        Guid addendumId,
        [FromBody] AcknowledgeAddendumRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new AcknowledgeAddendumCommand(id, addendumId, request.BidderId);
        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<object>.SuccessResponse(new { success = result }));
    }

    #endregion
}

/// <summary>
/// Request model for cancelling a tender.
/// </summary>
public class CancelTenderRequest
{
    /// <summary>
    /// Reason for cancellation.
    /// </summary>
    public string? Reason { get; set; }
}

/// <summary>
/// Request model for setting the pricing level.
/// </summary>
public class SetPricingLevelRequest
{
    /// <summary>
    /// The pricing level to set (Bill, Item, SubItem).
    /// </summary>
    public PricingLevel PricingLevel { get; set; }
}

/// <summary>
/// Request model for acknowledging an addendum.
/// </summary>
public class AcknowledgeAddendumRequest
{
    /// <summary>
    /// ID of the bidder acknowledging the addendum.
    /// </summary>
    public Guid BidderId { get; set; }
}

/// <summary>
/// Request model for updating bidder qualification status.
/// </summary>
public class UpdateBidderQualificationRequest
{
    /// <summary>
    /// The new qualification status (Qualified or Rejected).
    /// </summary>
    public string QualificationStatus { get; set; } = string.Empty;

    /// <summary>
    /// Optional reason for the qualification decision.
    /// </summary>
    public string? Reason { get; set; }
}
