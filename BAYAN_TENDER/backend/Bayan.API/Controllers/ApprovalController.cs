using Bayan.Application.Common.Models;
using Bayan.Application.Features.Approval.Commands.InitiateApproval;
using Bayan.Application.Features.Approval.Commands.SubmitApprovalDecision;
using Bayan.Application.Features.Approval.DTOs;
using Bayan.Application.Features.Approval.Queries.GetApprovalHistory;
using Bayan.Application.Features.Approval.Queries.GetApprovalStatus;
using Bayan.Application.Features.Approval.Queries.GetPendingApprovals;
using Bayan.Application.Features.Admin.Users;
using Bayan.Application.Features.Admin.Users.Queries.GetUsers;
using Bayan.API.Authorization;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing approval workflows.
/// </summary>
[ApiController]
[Route("api")]
[Authorize(Roles = BayanRoles.InternalUsers)]
public class ApprovalController : ControllerBase
{
    private readonly IMediator _mediator;

    public ApprovalController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Gets the approval status for a specific tender.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The approval workflow status if exists.</returns>
    [HttpGet("tenders/{id:guid}/approval")]
    [ProducesResponseType(typeof(ApprovalWorkflowDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ApprovalWorkflowDto>> GetApprovalStatus(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var query = new GetApprovalStatusQuery(id);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("No approval workflow found for this tender."));
        }

        return Ok(ApiResponse<ApprovalWorkflowDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Initiates an approval workflow for a tender.
    /// Creates approval_workflows record and approval_levels records (3 sequential levels).
    /// Notifies Level 1 approver via email.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="request">The initiation request with approver details.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created approval workflow.</returns>
    [HttpPost("tenders/{id:guid}/approval/initiate")]
    [Authorize(Roles = BayanRoles.ApprovalInitiators)]
    [ProducesResponseType(typeof(InitiateApprovalResult), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<InitiateApprovalResult>> InitiateApproval(
        Guid id,
        [FromBody] InitiateApprovalRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new InitiateApprovalCommand
        {
            TenderId = id,
            AwardPackPdfPath = request.AwardPackPdfPath,
            NumberOfLevels = request.NumberOfLevels,
            ApproverUserIds = request.ApproverUserIds,
            LevelDeadlines = request.LevelDeadlines,
            ApproverChangeReason = request.ApproverChangeReason
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetApprovalStatus), new { id }, ApiResponse<InitiateApprovalResult>.SuccessResponse(result));
    }

    /// <summary>
    /// Submits an approval decision for the current active level.
    /// Records decision (Approve, Reject, ReturnForRevision).
    /// Requires comment for Reject/ReturnForRevision.
    /// If Approve: progresses to next level or completes workflow.
    /// If Reject: marks workflow as rejected.
    /// If ReturnForRevision: sends back to Tender Manager.
    /// Final approval: sets tender status to Awarded.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="request">The decision request with decision type and comment.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result of the approval decision.</returns>
    [HttpPost("tenders/{id:guid}/approval/decide")]
    [Authorize(Roles = BayanRoles.ApprovalDeciders)]
    [ProducesResponseType(typeof(SubmitApprovalDecisionResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<SubmitApprovalDecisionResult>> SubmitApprovalDecision(
        Guid id,
        [FromBody] ApprovalDecisionDto request,
        CancellationToken cancellationToken = default)
    {
        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = id,
            Decision = request.Decision,
            Comment = request.Comment
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<SubmitApprovalDecisionResult>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the approval history for a specific tender.
    /// </summary>
    /// <param name="id">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The approval history for the tender.</returns>
    [HttpGet("tenders/{id:guid}/approval/history")]
    [ProducesResponseType(typeof(List<ApprovalHistoryDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<List<ApprovalHistoryDto>>> GetApprovalHistory(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var query = new GetApprovalHistoryQuery(id);
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<List<ApprovalHistoryDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets pending approvals for the current user (for dashboard integration).
    /// Returns approvals where the current user is the active approver.
    /// </summary>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="search">Optional search term for tender reference or title.</param>
    /// <param name="overdueOnly">Optional filter to show only overdue items.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of pending approvals.</returns>
    [HttpGet("approvals/pending")]
    [Authorize(Roles = BayanRoles.ApprovalDeciders)]
    [ProducesResponseType(typeof(PaginatedList<PendingApprovalDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<PendingApprovalDto>>> GetPendingApprovals(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] string? search = null,
        [FromQuery] bool? overdueOnly = null,
        CancellationToken cancellationToken = default)
    {
        var query = new GetPendingApprovalsQuery
        {
            Page = page,
            PageSize = pageSize,
            Search = search,
            OverdueOnly = overdueOnly
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<PendingApprovalDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets users with Approver role for approval workflow dropdowns.
    /// Accessible by Admin and TenderManager roles.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of active approver users.</returns>
    [HttpGet("approvers")]
    [Authorize(Roles = BayanRoles.ApprovalInitiators)]
    [ProducesResponseType(typeof(PaginatedList<UserDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<UserDto>>> GetApprovers(
        CancellationToken cancellationToken = default)
    {
        var query = new GetUsersQuery
        {
            Page = 1,
            PageSize = 100,
            Role = UserRole.Approver,
            IsActive = true
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<UserDto>>.SuccessResponse(result));
    }
}

/// <summary>
/// Request model for initiating an approval workflow.
/// </summary>
public class InitiateApprovalRequest
{
    /// <summary>
    /// Optional path to the award pack PDF in storage.
    /// </summary>
    public string? AwardPackPdfPath { get; set; }

    /// <summary>
    /// Number of approval levels. Defaults to 3 if not specified.
    /// Must be between 1 and 10.
    /// </summary>
    public int? NumberOfLevels { get; set; }

    /// <summary>
    /// List of approver user IDs in sequential order.
    /// Count must match NumberOfLevels (or default of 3).
    /// </summary>
    public List<Guid> ApproverUserIds { get; set; } = new();

    /// <summary>
    /// Optional deadlines for each approval level.
    /// If provided, count must match NumberOfLevels (or default of 3).
    /// </summary>
    public List<DateTime?>? LevelDeadlines { get; set; }

    /// <summary>
    /// Optional reason for changing approvers during re-initiation.
    /// Required when approver route differs from previous returned/rejected workflow.
    /// </summary>
    public string? ApproverChangeReason { get; set; }
}
