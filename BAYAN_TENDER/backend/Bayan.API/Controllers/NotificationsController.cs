using Bayan.Application.Common.Models;
using Bayan.Application.Features.Notifications.Commands.UpdateNotificationPreferences;
using Bayan.Application.Features.Notifications.DTOs;
using Bayan.Application.Features.Notifications.Queries.GetNotificationPreferences;
using Bayan.API.Authorization;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing notification preferences.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = BayanRoles.InternalUsers)]
public class NotificationsController : ControllerBase
{
    private readonly IMediator _mediator;

    public NotificationsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Gets the current user's notification preferences.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The user's notification preferences.</returns>
    [HttpGet("preferences")]
    [ProducesResponseType(typeof(NotificationPreferencesDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<NotificationPreferencesDto>> GetPreferences(
        CancellationToken cancellationToken = default)
    {
        var query = new GetNotificationPreferencesQuery();
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<NotificationPreferencesDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Updates the current user's notification preferences.
    /// </summary>
    /// <param name="request">The notification preferences to update.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated notification preferences.</returns>
    [HttpPut("preferences")]
    [ProducesResponseType(typeof(NotificationPreferencesDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<NotificationPreferencesDto>> UpdatePreferences(
        [FromBody] UpdateNotificationPreferencesRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateNotificationPreferencesCommand
        {
            TenderInvitation = request.TenderInvitation,
            AddendumIssued = request.AddendumIssued,
            ClarificationPublished = request.ClarificationPublished,
            DeadlineReminder3Days = request.DeadlineReminder3Days,
            DeadlineReminder1Day = request.DeadlineReminder1Day,
            ApprovalRequest = request.ApprovalRequest
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<NotificationPreferencesDto>.SuccessResponse(result));
    }
}

/// <summary>
/// Request DTO for updating notification preferences.
/// </summary>
public record UpdateNotificationPreferencesRequest
{
    /// <summary>
    /// Receive tender invitation notifications.
    /// </summary>
    public bool TenderInvitation { get; init; } = true;

    /// <summary>
    /// Receive addendum issued notifications.
    /// </summary>
    public bool AddendumIssued { get; init; } = true;

    /// <summary>
    /// Receive clarification published notifications.
    /// </summary>
    public bool ClarificationPublished { get; init; } = true;

    /// <summary>
    /// Receive 3-day deadline reminders.
    /// </summary>
    public bool DeadlineReminder3Days { get; init; } = true;

    /// <summary>
    /// Receive 1-day deadline reminders.
    /// </summary>
    public bool DeadlineReminder1Day { get; init; } = true;

    /// <summary>
    /// Receive approval request notifications.
    /// </summary>
    public bool ApprovalRequest { get; init; } = true;
}
