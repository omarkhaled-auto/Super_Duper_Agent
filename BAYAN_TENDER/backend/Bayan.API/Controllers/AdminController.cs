using Bayan.Application.Common.Models;
using Bayan.Application.Features.Admin.AuditLogs.DTOs;
using Bayan.Application.Features.Admin.AuditLogs.Queries.GetAuditLogs;
using Bayan.Application.Features.Admin.Settings.Commands.UpdateSetting;
using Bayan.Application.Features.Admin.Settings.DTOs;
using Bayan.Application.Features.Admin.Settings.Queries.GetSettings;
using Bayan.Application.Features.Admin.Users;
using Bayan.Application.Features.Admin.Users.Commands.CreateUser;
using Bayan.Application.Features.Admin.Users.Commands.ToggleUserActive;
using Bayan.Application.Features.Admin.Users.Commands.UpdateUser;
using Bayan.Application.Features.Admin.Users.Queries.GetUserById;
using Bayan.Application.Features.Admin.Users.Queries.GetUsers;
using Bayan.Domain.Enums;
using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for administrative operations including user management.
/// </summary>
[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class AdminController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly IApplicationDbContext _context;

    public AdminController(IMediator mediator, IApplicationDbContext context)
    {
        _mediator = mediator;
        _context = context;
    }

    #region User Management

    /// <summary>
    /// Gets a paginated list of users with optional search and filtering.
    /// </summary>
    /// <param name="page">Page number (1-based). Default is 1.</param>
    /// <param name="pageSize">Number of items per page. Default is 10.</param>
    /// <param name="search">Optional search term for filtering by name, email, or company.</param>
    /// <param name="role">Optional filter by user role.</param>
    /// <param name="isActive">Optional filter for active status.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of users.</returns>
    [HttpGet("users")]
    [ProducesResponseType(typeof(PaginatedList<UserDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<UserDto>>> GetUsers(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] string? search = null,
        [FromQuery] UserRole? role = null,
        [FromQuery] bool? isActive = null,
        CancellationToken cancellationToken = default)
    {
        var query = new GetUsersQuery
        {
            Page = page,
            PageSize = pageSize,
            Search = search,
            Role = role,
            IsActive = isActive
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<UserDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets a user by ID.
    /// </summary>
    /// <param name="id">The user's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The user if found.</returns>
    [HttpGet("users/{id:guid}")]
    [ProducesResponseType(typeof(UserDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<UserDto>> GetUser(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var query = new GetUserByIdQuery(id);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("User not found."));
        }

        return Ok(ApiResponse<UserDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Creates a new user.
    /// </summary>
    /// <param name="request">The user creation request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result of the user creation including the user ID.</returns>
    [HttpPost("users")]
    [ProducesResponseType(typeof(CreateUserResult), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<CreateUserResult>> CreateUser(
        [FromBody] CreateUserRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new CreateUserCommand
        {
            FirstName = request.FirstName,
            LastName = request.LastName,
            Email = request.Email,
            Role = request.Role,
            Phone = request.Phone,
            CompanyName = request.CompanyName,
            Department = request.Department,
            JobTitle = request.JobTitle,
            SendInvitationEmail = request.SendInvitationEmail,
            Password = request.Password
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetUser), new { id = result.UserId }, ApiResponse<CreateUserResult>.SuccessResponse(result));
    }

    /// <summary>
    /// Updates an existing user.
    /// </summary>
    /// <param name="id">The user's unique identifier.</param>
    /// <param name="request">The updated user data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>No content if successful.</returns>
    [HttpPut("users/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> UpdateUser(
        Guid id,
        [FromBody] UpdateUserRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateUserCommand
        {
            Id = id,
            FirstName = request.FirstName,
            LastName = request.LastName,
            Email = request.Email,
            Role = request.Role,
            Phone = request.Phone,
            CompanyName = request.CompanyName,
            Department = request.Department,
            JobTitle = request.JobTitle,
            PreferredLanguage = request.PreferredLanguage,
            TimeZone = request.TimeZone
        };

        var success = await _mediator.Send(command, cancellationToken);

        if (!success)
        {
            return NotFound(ApiResponse<object>.FailureResponse("User not found."));
        }

        return NoContent();
    }

    /// <summary>
    /// Toggles a user's active status.
    /// </summary>
    /// <param name="id">The user's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The result of the toggle operation including the new active status.</returns>
    [HttpPost("users/{id:guid}/toggle-active")]
    [ProducesResponseType(typeof(ToggleUserActiveResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ToggleUserActiveResult>> ToggleUserActive(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        var command = new ToggleUserActiveCommand(id);
        var result = await _mediator.Send(command, cancellationToken);

        if (!result.Success)
        {
            return NotFound(ApiResponse<object>.FailureResponse(result.ErrorMessage ?? "User not found."));
        }

        return Ok(ApiResponse<ToggleUserActiveResult>.SuccessResponse(result));
    }

    /// <summary>
    /// Deletes a user by ID. Cannot delete yourself.
    /// </summary>
    [HttpDelete("users/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> DeleteUser(
        Guid id,
        CancellationToken cancellationToken = default)
    {
        // Prevent self-deletion
        var currentUserIdClaim = User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
        if (Guid.TryParse(currentUserIdClaim, out var currentUserId) && currentUserId == id)
        {
            return BadRequest(ApiResponse<object>.FailureResponse("You cannot delete your own account."));
        }

        var user = await _context.Users.FindAsync(new object[] { id }, cancellationToken);
        if (user == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("User not found."));
        }

        _context.Users.Remove(user);
        await _context.SaveChangesAsync(cancellationToken);

        return NoContent();
    }

    #endregion

    #region System Settings

    /// <summary>
    /// Gets all system settings and units of measure.
    /// </summary>
    /// <param name="category">Optional category filter for settings.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>All system settings and units of measure.</returns>
    [HttpGet("settings")]
    [ProducesResponseType(typeof(GetSettingsResponse), StatusCodes.Status200OK)]
    public async Task<ActionResult<GetSettingsResponse>> GetSettings(
        [FromQuery] string? category = null,
        CancellationToken cancellationToken = default)
    {
        var query = new GetSettingsQuery { Category = category };
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<GetSettingsResponse>.SuccessResponse(result));
    }

    /// <summary>
    /// Updates a system setting by key.
    /// </summary>
    /// <param name="key">The setting key to update.</param>
    /// <param name="request">The update request containing the new value.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated setting if successful.</returns>
    [HttpPut("settings/{key}")]
    [ProducesResponseType(typeof(SystemSettingDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<SystemSettingDto>> UpdateSetting(
        string key,
        [FromBody] UpdateSettingRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateSettingCommand
        {
            Key = key,
            Value = request.Value
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (!result.Success)
        {
            if (result.ErrorMessage?.Contains("not found") == true)
            {
                return NotFound(ApiResponse<object>.FailureResponse(result.ErrorMessage ?? "Setting not found."));
            }
            return BadRequest(ApiResponse<object>.FailureResponse(result.ErrorMessage ?? "Bad request"));
        }

        return Ok(ApiResponse<SystemSettingDto>.SuccessResponse(result.Setting));
    }

    #endregion

    #region Audit Logs

    /// <summary>
    /// Gets a paginated list of audit logs with optional filtering.
    /// </summary>
    /// <param name="page">Page number (1-based). Default is 1.</param>
    /// <param name="pageSize">Number of items per page. Default is 20.</param>
    /// <param name="userId">Optional filter by user ID.</param>
    /// <param name="action">Optional filter by action type.</param>
    /// <param name="entityType">Optional filter by entity type.</param>
    /// <param name="entityId">Optional filter by specific entity ID.</param>
    /// <param name="startDate">Optional filter by start date (inclusive).</param>
    /// <param name="endDate">Optional filter by end date (inclusive).</param>
    /// <param name="search">Optional search term for filtering by user email or action.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of audit logs.</returns>
    [HttpGet("audit-logs")]
    [Authorize(Roles = "Admin,Auditor")]
    [ProducesResponseType(typeof(PaginatedList<AuditLogDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<AuditLogDto>>> GetAuditLogs(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] Guid? userId = null,
        [FromQuery] string? action = null,
        [FromQuery] string? entityType = null,
        [FromQuery] Guid? entityId = null,
        [FromQuery] DateTime? startDate = null,
        [FromQuery] DateTime? endDate = null,
        [FromQuery] string? search = null,
        CancellationToken cancellationToken = default)
    {
        var query = new GetAuditLogsQuery
        {
            Page = page,
            PageSize = pageSize,
            UserId = userId,
            Action = action,
            EntityType = entityType,
            EntityId = entityId,
            StartDate = startDate,
            EndDate = endDate,
            Search = search
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<AuditLogDto>>.SuccessResponse(result));
    }

    #endregion
}

#region Request DTOs

/// <summary>
/// Request DTO for creating a new user.
/// </summary>
public record CreateUserRequest
{
    /// <summary>
    /// User's first name.
    /// </summary>
    public string FirstName { get; init; } = string.Empty;

    /// <summary>
    /// User's last name.
    /// </summary>
    public string LastName { get; init; } = string.Empty;

    /// <summary>
    /// User's email address.
    /// </summary>
    public string Email { get; init; } = string.Empty;

    /// <summary>
    /// User's role in the system.
    /// </summary>
    public UserRole Role { get; init; }

    /// <summary>
    /// User's phone number.
    /// </summary>
    public string? Phone { get; init; }

    /// <summary>
    /// Company name (for bidder users).
    /// </summary>
    public string? CompanyName { get; init; }

    /// <summary>
    /// Department or organizational unit.
    /// </summary>
    public string? Department { get; init; }

    /// <summary>
    /// Job title or position.
    /// </summary>
    public string? JobTitle { get; init; }

    /// <summary>
    /// Whether to send an invitation email with the temporary password. Default is true.
    /// </summary>
    public bool SendInvitationEmail { get; init; } = true;

    /// <summary>
    /// Optional admin-provided password. If set, uses this instead of generating a temporary password.
    /// </summary>
    public string? Password { get; init; }
}

/// <summary>
/// Request DTO for updating an existing user.
/// </summary>
public record UpdateUserRequest
{
    /// <summary>
    /// User's first name.
    /// </summary>
    public string FirstName { get; init; } = string.Empty;

    /// <summary>
    /// User's last name.
    /// </summary>
    public string LastName { get; init; } = string.Empty;

    /// <summary>
    /// User's email address.
    /// </summary>
    public string Email { get; init; } = string.Empty;

    /// <summary>
    /// User's role in the system.
    /// </summary>
    public UserRole Role { get; init; }

    /// <summary>
    /// User's phone number.
    /// </summary>
    public string? Phone { get; init; }

    /// <summary>
    /// Company name (for bidder users).
    /// </summary>
    public string? CompanyName { get; init; }

    /// <summary>
    /// Department or organizational unit.
    /// </summary>
    public string? Department { get; init; }

    /// <summary>
    /// Job title or position.
    /// </summary>
    public string? JobTitle { get; init; }

    /// <summary>
    /// User's preferred language.
    /// </summary>
    public string? PreferredLanguage { get; init; }

    /// <summary>
    /// User's timezone.
    /// </summary>
    public string? TimeZone { get; init; }
}

/// <summary>
/// Request DTO for updating a system setting.
/// </summary>
public record UpdateSettingRequest
{
    /// <summary>
    /// The new value for the setting.
    /// </summary>
    public string Value { get; init; } = string.Empty;
}

#endregion
