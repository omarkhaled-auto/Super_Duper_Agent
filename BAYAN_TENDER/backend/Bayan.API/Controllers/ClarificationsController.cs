using Bayan.Application.Common.Models;
using Bayan.Application.Features.Clarifications.Commands.ApproveAnswer;
using Bayan.Application.Features.Clarifications.Commands.AssignClarification;
using Bayan.Application.Features.Clarifications.Commands.DraftAnswer;
using Bayan.Application.Features.Clarifications.Commands.MarkDuplicate;
using Bayan.Application.Features.Clarifications.Commands.PublishBulletin;
using Bayan.Application.Features.Clarifications.Commands.RejectClarification;
using Bayan.Application.Features.Clarifications.Commands.SubmitClarification;
using Bayan.Application.Features.Clarifications.Commands.SubmitInternalRfi;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Application.Features.Clarifications.Queries.DownloadBulletin;
using Bayan.Application.Features.Clarifications.Queries.GetClarificationById;
using Bayan.Application.Features.Clarifications.Queries.GetClarificationBulletins;
using Bayan.Application.Features.Clarifications.Queries.GetClarifications;
using Bayan.Application.Features.Clarifications.Queries.GetNextClarificationRef;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing clarifications and RFIs for tenders.
/// </summary>
[ApiController]
[Route("api/tenders/{tenderId:guid}/clarifications")]
[Authorize(Roles = "Admin,TenderManager")]
public class ClarificationsController : ControllerBase
{
    private readonly IMediator _mediator;

    public ClarificationsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Gets the current user ID from claims.
    /// </summary>
    private Guid GetCurrentUserId()
    {
        var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value
            ?? User.FindFirst("sub")?.Value;

        if (string.IsNullOrEmpty(userIdClaim) || !Guid.TryParse(userIdClaim, out var userId))
        {
            throw new UnauthorizedAccessException("User ID not found in claims.");
        }

        return userId;
    }

    /// <summary>
    /// Gets a paginated list of clarifications for a tender with optional filtering.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="status">Optional filter by status.</param>
    /// <param name="type">Optional filter by type.</param>
    /// <param name="section">Optional filter by BOQ section.</param>
    /// <param name="priority">Optional filter by priority.</param>
    /// <param name="bidderId">Optional filter by bidder ID.</param>
    /// <param name="search">Optional search term.</param>
    /// <param name="sortBy">Sort field.</param>
    /// <param name="sortDescending">Sort direction.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of clarifications.</returns>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<ClarificationDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<ClarificationDto>>> GetClarifications(
        Guid tenderId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] ClarificationStatus? status = null,
        [FromQuery] ClarificationType? type = null,
        [FromQuery] string? section = null,
        [FromQuery] ClarificationPriority? priority = null,
        [FromQuery] Guid? bidderId = null,
        [FromQuery] string? search = null,
        [FromQuery] string sortBy = "SubmittedAt",
        [FromQuery] bool sortDescending = true,
        CancellationToken cancellationToken = default)
    {
        var query = new GetClarificationsQuery
        {
            TenderId = tenderId,
            Page = page,
            PageSize = pageSize,
            Status = status,
            Type = type,
            Section = section,
            Priority = priority,
            BidderId = bidderId,
            Search = search,
            SortBy = sortBy,
            SortDescending = sortDescending
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<ClarificationDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets a clarification by ID with full details.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="id">The clarification's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The clarification details if found.</returns>
    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(ClarificationDetailDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationDetailDto>> GetClarification(
        Guid tenderId,
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var query = new GetClarificationByIdQuery(tenderId, id);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Clarification not found"));
        }

        return Ok(ApiResponse<ClarificationDetailDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the next available clarification reference number.
    /// Format: CL-{3-digit-sequence}
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The next clarification reference number.</returns>
    [HttpGet("next-reference")]
    [ProducesResponseType(typeof(string), StatusCodes.Status200OK)]
    public async Task<ActionResult<string>> GetNextReference(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        var query = new GetNextClarificationRefQuery(tenderId);
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<string>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets all clarification bulletins for a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of clarification bulletins.</returns>
    [HttpGet("bulletins")]
    [ProducesResponseType(typeof(List<ClarificationBulletinDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<List<ClarificationBulletinDto>>> GetBulletins(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        var query = new GetClarificationBulletinsQuery(tenderId);
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<List<ClarificationBulletinDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Creates and publishes a new clarification bulletin.
    /// This operation:
    /// - Auto-increments bulletin number (QB-001, QB-002, etc.)
    /// - Generates a PDF document with Q&amp;A content using QuestPDF
    /// - Stores the PDF in MinIO at tender-documents/{tenderId}/Clarifications/
    /// - Updates selected clarifications to 'Published' status
    /// - Sends email notifications with PDF attachment to all qualified bidders
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="dto">The bulletin creation data containing clarification IDs and optional introduction/closing notes.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created bulletin with all questions included.</returns>
    [HttpPost("bulletins")]
    [ProducesResponseType(typeof(ClarificationBulletinDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationBulletinDto>> PublishBulletin(
        Guid tenderId,
        [FromBody] CreateBulletinDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new PublishBulletinCommand(tenderId, dto);
        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(
            nameof(DownloadBulletin),
            new { tenderId, bulletinId = result.Id },
            ApiResponse<ClarificationBulletinDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Downloads the PDF for a specific bulletin.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bulletinId">The bulletin's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The bulletin PDF file.</returns>
    [HttpGet("bulletins/{bulletinId:guid}/download")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DownloadBulletin(
        Guid tenderId,
        Guid bulletinId,
        CancellationToken cancellationToken = default)
    {
        var query = new DownloadBulletinQuery(tenderId, bulletinId);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Bulletin not found"));
        }

        return File(result.Content, result.ContentType, result.FileName);
    }

    /// <summary>
    /// Submits a new clarification question from a bidder.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="dto">The clarification data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created clarification.</returns>
    [HttpPost]
    [ProducesResponseType(typeof(ClarificationDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationDto>> SubmitClarification(
        Guid tenderId,
        [FromBody] CreateClarificationDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new SubmitClarificationCommand
        {
            TenderId = tenderId,
            Subject = dto.Subject,
            Question = dto.Question,
            RelatedBoqSection = dto.RelatedBoqSection,
            RelatedDocumentId = dto.RelatedDocumentId,
            BidderId = dto.BidderId,
            AttachmentIds = dto.AttachmentIds,
            IsAnonymous = dto.IsAnonymous
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetClarification), new { tenderId, id = result.Id }, ApiResponse<ClarificationDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Submits an internal RFI from the tender team.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="dto">The internal RFI data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created internal RFI.</returns>
    [HttpPost("internal-rfi")]
    [ProducesResponseType(typeof(ClarificationDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationDto>> SubmitInternalRfi(
        Guid tenderId,
        [FromBody] CreateInternalRfiDto dto,
        CancellationToken cancellationToken = default)
    {
        var userId = GetCurrentUserId();

        var command = new SubmitInternalRfiCommand
        {
            TenderId = tenderId,
            UserId = userId,
            Subject = dto.Subject,
            Question = dto.Question,
            RelatedBoqSection = dto.RelatedBoqSection,
            RelatedDocumentId = dto.RelatedDocumentId,
            Priority = dto.Priority,
            AttachmentIds = dto.AttachmentIds
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetClarification), new { tenderId, id = result.Id }, ApiResponse<ClarificationDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Drafts an answer to a clarification.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="id">The clarification's unique identifier.</param>
    /// <param name="dto">The draft answer data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated clarification.</returns>
    [HttpPost("{id:guid}/answer")]
    [ProducesResponseType(typeof(ClarificationDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationDto>> DraftAnswer(
        Guid tenderId,
        Guid id,
        [FromBody] DraftAnswerDto dto,
        CancellationToken cancellationToken = default)
    {
        var userId = GetCurrentUserId();

        var command = new DraftAnswerCommand
        {
            TenderId = tenderId,
            ClarificationId = id,
            UserId = userId,
            Answer = dto.Answer
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ClarificationDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Approves a drafted answer, changing status to Answered.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="id">The clarification's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated clarification.</returns>
    [HttpPost("{id:guid}/approve")]
    [ProducesResponseType(typeof(ClarificationDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationDto>> ApproveAnswer(
        Guid tenderId,
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var userId = GetCurrentUserId();

        var command = new ApproveAnswerCommand(tenderId, id, userId);
        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ClarificationDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Marks a clarification as duplicate of another.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="id">The clarification's unique identifier.</param>
    /// <param name="dto">The duplicate marking data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated clarification.</returns>
    [HttpPost("{id:guid}/duplicate")]
    [ProducesResponseType(typeof(ClarificationDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationDto>> MarkDuplicate(
        Guid tenderId,
        Guid id,
        [FromBody] MarkDuplicateDto dto,
        CancellationToken cancellationToken = default)
    {
        var userId = GetCurrentUserId();

        var command = new MarkDuplicateCommand
        {
            TenderId = tenderId,
            ClarificationId = id,
            OriginalClarificationId = dto.OriginalClarificationId,
            UserId = userId
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ClarificationDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Rejects a clarification with a reason.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="id">The clarification's unique identifier.</param>
    /// <param name="dto">The rejection data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated clarification.</returns>
    [HttpPost("{id:guid}/reject")]
    [ProducesResponseType(typeof(ClarificationDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationDto>> RejectClarification(
        Guid tenderId,
        Guid id,
        [FromBody] RejectClarificationDto dto,
        CancellationToken cancellationToken = default)
    {
        var userId = GetCurrentUserId();

        var command = new RejectClarificationCommand
        {
            TenderId = tenderId,
            ClarificationId = id,
            UserId = userId,
            Reason = dto.Reason
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ClarificationDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Assigns a clarification to a team member.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="id">The clarification's unique identifier.</param>
    /// <param name="dto">The assignment data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated clarification.</returns>
    [HttpPost("{id:guid}/assign")]
    [ProducesResponseType(typeof(ClarificationDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ClarificationDto>> AssignClarification(
        Guid tenderId,
        Guid id,
        [FromBody] AssignClarificationDto dto,
        CancellationToken cancellationToken = default)
    {
        var userId = GetCurrentUserId();

        var command = new AssignClarificationCommand
        {
            TenderId = tenderId,
            ClarificationId = id,
            AssignToUserId = dto.AssignToUserId,
            AssignedByUserId = userId
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ClarificationDto>.SuccessResponse(result));
    }
}
