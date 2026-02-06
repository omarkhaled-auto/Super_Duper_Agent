using Bayan.Application.Common.Models;
using Bayan.Application.Features.Dashboard.DTOs;
using Bayan.Application.Features.Dashboard.Queries.GetApproverDashboard;
using Bayan.Application.Features.Dashboard.Queries.GetOverviewDashboard;
using Bayan.Application.Features.Dashboard.Queries.GetTenderManagerDashboard;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for dashboard data endpoints.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class DashboardController : ControllerBase
{
    private readonly IMediator _mediator;

    public DashboardController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Gets the Tender Manager dashboard data including KPIs, active tenders, deadlines, and activity feed.
    /// </summary>
    /// <param name="deadlineDaysAhead">Number of days to look ahead for upcoming deadlines (default: 7).</param>
    /// <param name="activityLimit">Maximum number of recent activities to return (default: 10).</param>
    /// <param name="activeTendersLimit">Maximum number of active tenders to return (default: 5).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The Tender Manager dashboard data.</returns>
    [HttpGet("tender-manager")]
    [ProducesResponseType(typeof(TenderManagerDashboardDto), StatusCodes.Status200OK)]
    public async Task<ActionResult<TenderManagerDashboardDto>> GetTenderManagerDashboard(
        [FromQuery] int deadlineDaysAhead = 7,
        [FromQuery] int activityLimit = 10,
        [FromQuery] int activeTendersLimit = 5,
        CancellationToken cancellationToken = default)
    {
        var query = new GetTenderManagerDashboardQuery
        {
            DeadlineDaysAhead = deadlineDaysAhead,
            ActivityLimit = activityLimit,
            ActiveTendersLimit = activeTendersLimit
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<TenderManagerDashboardDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets a high-level overview dashboard with tender counts by status, bidder stats,
    /// pending approvals, total contract value, and a monthly trend.
    /// </summary>
    /// <param name="monthsBack">Number of months to include in the monthly trend (default: 6).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The overview dashboard data.</returns>
    [HttpGet("overview")]
    [ProducesResponseType(typeof(ApiResponse<OverviewDashboardDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<OverviewDashboardDto>> GetOverviewDashboard(
        [FromQuery] int monthsBack = 6,
        CancellationToken cancellationToken = default)
    {
        var query = new GetOverviewDashboardQuery { MonthsBack = monthsBack };
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<OverviewDashboardDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the Approver dashboard data including pending approvals, recent decisions, and statistics.
    /// Returns data specific to the currently authenticated user.
    /// </summary>
    /// <param name="recentDecisionsLimit">Maximum number of recent decisions to return (default: 10).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The Approver dashboard data.</returns>
    [HttpGet("approver")]
    [ProducesResponseType(typeof(ApproverDashboardDto), StatusCodes.Status200OK)]
    public async Task<ActionResult<ApproverDashboardDto>> GetApproverDashboard(
        [FromQuery] int recentDecisionsLimit = 10,
        CancellationToken cancellationToken = default)
    {
        var query = new GetApproverDashboardQuery
        {
            RecentDecisionsLimit = recentDecisionsLimit
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<ApproverDashboardDto>.SuccessResponse(result));
    }
}
