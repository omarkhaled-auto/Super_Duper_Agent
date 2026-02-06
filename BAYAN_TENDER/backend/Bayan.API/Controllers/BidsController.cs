using Bayan.Application.Common.Models;
using Bayan.Application.Features.Bids.Commands.AcceptLateBid;
using Bayan.Application.Features.Bids.Commands.DisqualifyBid;
using Bayan.Application.Features.Bids.Commands.DownloadAllBids;
using Bayan.Application.Features.Bids.Commands.OpenBids;
using Bayan.Application.Features.Bids.Commands.RejectLateBid;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Application.Features.Bids.Queries.GetBidDetails;
using Bayan.Application.Features.Bids.Queries.GetBids;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing bids (internal operations).
/// </summary>
[ApiController]
[Route("api/tenders/{tenderId:guid}/bids")]
[Authorize(Roles = "Admin,TenderManager")]
public class BidsController : ControllerBase
{
    private readonly IMediator _mediator;

    public BidsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Gets a paginated list of bids for a tender with optional filtering.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="status">Optional filter by bid status.</param>
    /// <param name="isLate">Optional filter by late submissions.</param>
    /// <param name="lateAccepted">Optional filter by late acceptance status.</param>
    /// <param name="search">Optional search term for bidder name.</param>
    /// <param name="sortBy">Sort field (default: SubmissionTime).</param>
    /// <param name="sortDescending">Sort direction (default: descending).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of bids.</returns>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<BidListDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<PaginatedList<BidListDto>>> GetBids(
        Guid tenderId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] BidSubmissionStatus? status = null,
        [FromQuery] bool? isLate = null,
        [FromQuery] bool? lateAccepted = null,
        [FromQuery] string? search = null,
        [FromQuery] string sortBy = "SubmissionTime",
        [FromQuery] bool sortDescending = true,
        CancellationToken cancellationToken = default)
    {
        var query = new GetBidsQuery
        {
            TenderId = tenderId,
            Page = page,
            PageSize = pageSize,
            Status = status,
            IsLate = isLate,
            LateAccepted = lateAccepted,
            Search = search,
            SortBy = sortBy,
            SortDescending = sortDescending
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<BidListDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets full details of a specific bid including all files.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The bid details if found.</returns>
    [HttpGet("{bidId:guid}")]
    [ProducesResponseType(typeof(BidDetailDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BidDetailDto>> GetBidDetails(
        Guid tenderId,
        Guid bidId,
        CancellationToken cancellationToken = default)
    {
        var query = new GetBidDetailsQuery(tenderId, bidId);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Bid not found"));
        }

        return Ok(ApiResponse<BidDetailDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Opens all bids for a tender.
    /// WARNING: This is an IRREVERSIBLE action.
    /// All bid amounts will be revealed and the action will be logged.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result of the bid opening operation.</returns>
    [HttpPost("open")]
    [ProducesResponseType(typeof(OpenBidsResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<OpenBidsResultDto>> OpenBids(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        var command = new OpenBidsCommand(tenderId);
        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<OpenBidsResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Accepts a late bid submission.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result of the late bid acceptance.</returns>
    [HttpPost("{bidId:guid}/accept-late")]
    [ProducesResponseType(typeof(LateBidDecisionDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<LateBidDecisionDto>> AcceptLateBid(
        Guid tenderId,
        Guid bidId,
        CancellationToken cancellationToken = default)
    {
        var command = new AcceptLateBidCommand(tenderId, bidId);
        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<LateBidDecisionDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Rejects a late bid submission.
    /// Sends a notification to the bidder.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid's unique identifier.</param>
    /// <param name="request">The rejection details.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result of the late bid rejection.</returns>
    [HttpPost("{bidId:guid}/reject-late")]
    [ProducesResponseType(typeof(LateBidDecisionDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<LateBidDecisionDto>> RejectLateBid(
        Guid tenderId,
        Guid bidId,
        [FromBody] RejectLateBidRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new RejectLateBidCommand
        {
            TenderId = tenderId,
            BidId = bidId,
            Reason = request.Reason
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<LateBidDecisionDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Disqualifies a bid submission.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid's unique identifier.</param>
    /// <param name="request">The disqualification details.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result of the disqualification.</returns>
    [HttpPost("{bidId:guid}/disqualify")]
    [ProducesResponseType(typeof(DisqualifyBidResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<DisqualifyBidResultDto>> DisqualifyBid(
        Guid tenderId,
        Guid bidId,
        [FromBody] DisqualifyBidRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new DisqualifyBidCommand
        {
            TenderId = tenderId,
            BidId = bidId,
            Reason = request.Reason
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<DisqualifyBidResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Downloads all bid documents as a ZIP file.
    /// Structure: {BidderName}/Commercial/..., {BidderName}/Technical/...
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A presigned URL to download the ZIP file.</returns>
    [HttpGet("download-all")]
    [ProducesResponseType(typeof(DownloadAllBidsResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<DownloadAllBidsResultDto>> DownloadAllBids(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        var command = new DownloadAllBidsCommand(tenderId);
        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<DownloadAllBidsResultDto>.SuccessResponse(result));
    }
}

/// <summary>
/// Request model for rejecting a late bid.
/// </summary>
public class RejectLateBidRequest
{
    /// <summary>
    /// Reason for rejection.
    /// </summary>
    public string Reason { get; set; } = string.Empty;
}

/// <summary>
/// Request model for disqualifying a bid.
/// </summary>
public class DisqualifyBidRequest
{
    /// <summary>
    /// Reason for disqualification.
    /// </summary>
    public string Reason { get; set; } = string.Empty;
}
