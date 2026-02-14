using Bayan.Application.Common.Models;
using Bayan.Application.Features.Auth.Commands.ForgotPassword;
using Bayan.Application.Features.Auth.Commands.Login;
using Bayan.Application.Features.Auth.Commands.RefreshToken;
using Bayan.Application.Features.Auth.Commands.ResetPassword;
using Bayan.Application.Features.Auth.DTOs;
using Bayan.Application.Features.Auth.Queries.GetCurrentUser;
using Bayan.API.Authorization;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for authentication operations.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly IConfiguration _configuration;

    public AuthController(IMediator mediator, IConfiguration configuration)
    {
        _mediator = mediator;
        _configuration = configuration;
    }

    /// <summary>
    /// Authenticates a user and returns JWT tokens.
    /// </summary>
    /// <param name="request">Login credentials.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Login response with tokens and user info.</returns>
    [HttpPost("login")]
    [AllowAnonymous]
    [ProducesResponseType(typeof(LoginResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<LoginResponseDto>> Login(
        [FromBody] LoginRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new LoginCommand
        {
            Email = request.Email,
            Password = request.Password,
            RememberMe = request.RememberMe,
            IpAddress = GetClientIpAddress()
        };

        try
        {
            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<LoginResponseDto>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Refreshes JWT tokens using a valid refresh token.
    /// </summary>
    /// <param name="request">Refresh token request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>New tokens.</returns>
    [HttpPost("refresh-token")]
    [AllowAnonymous]
    [ProducesResponseType(typeof(TokenDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<TokenDto>> RefreshToken(
        [FromBody] RefreshTokenRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new RefreshTokenCommand
        {
            RefreshToken = request.RefreshToken,
            IpAddress = GetClientIpAddress()
        };

        try
        {
            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<TokenDto>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Initiates the forgot password flow by sending a reset email.
    /// </summary>
    /// <param name="request">Forgot password request containing email.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Success response (always returns success to prevent email enumeration).</returns>
    [HttpPost("forgot-password")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public async Task<IActionResult> ForgotPassword(
        [FromBody] ForgotPasswordRequest request,
        CancellationToken cancellationToken = default)
    {
        var frontendUrl = _configuration["FrontendUrl"] ?? "http://localhost:3000";
        var resetUrl = $"{frontendUrl}/reset-password";

        var command = new ForgotPasswordCommand
        {
            Email = request.Email,
            ResetUrl = resetUrl
        };

        await _mediator.Send(command, cancellationToken);

        // Always return success to prevent email enumeration attacks
        return Ok(ApiResponse<object>.SuccessResponse(new { message = "If an account with that email exists, a password reset link has been sent." }));
    }

    /// <summary>
    /// Resets user password using a valid reset token.
    /// </summary>
    /// <param name="request">Reset password request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Success response.</returns>
    [HttpPost("reset-password")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> ResetPassword(
        [FromBody] ResetPasswordRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new ResetPasswordCommand
        {
            Email = request.Email,
            Token = request.Token,
            NewPassword = request.NewPassword,
            ConfirmPassword = request.ConfirmPassword
        };

        try
        {
            await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<object>.SuccessResponse(new { message = "Password has been reset successfully." }));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Gets the currently authenticated user's information.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Current user's information.</returns>
    [HttpGet("me")]
    [Authorize(Roles = BayanRoles.InternalUsers)]
    [ProducesResponseType(typeof(UserDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<UserDto>> GetCurrentUser(
        CancellationToken cancellationToken = default)
    {
        try
        {
            var result = await _mediator.Send(new GetCurrentUserQuery(), cancellationToken);
            return Ok(ApiResponse<UserDto>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Logs out the current user.
    /// For JWT-based auth, this is a no-op on the server side — the client
    /// is responsible for clearing the stored tokens.
    /// </summary>
    /// <returns>Success response.</returns>
    [HttpPost("logout")]
    [Authorize]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public IActionResult Logout()
    {
        // JWT tokens are stateless — server-side invalidation would require
        // a token blacklist. For now, the client clears its stored tokens.
        return Ok(ApiResponse<object>.SuccessResponse(new { message = "Logged out successfully." }));
    }

    /// <summary>
    /// Gets the client IP address from the request.
    /// </summary>
    private string? GetClientIpAddress()
    {
        // Check for forwarded headers (when behind a proxy/load balancer)
        var forwardedFor = HttpContext.Request.Headers["X-Forwarded-For"].FirstOrDefault();
        if (!string.IsNullOrEmpty(forwardedFor))
        {
            // Take the first IP address if there are multiple
            return forwardedFor.Split(',').First().Trim();
        }

        // Check for real IP header (Nginx)
        var realIp = HttpContext.Request.Headers["X-Real-IP"].FirstOrDefault();
        if (!string.IsNullOrEmpty(realIp))
        {
            return realIp;
        }

        // Fall back to connection remote IP
        return HttpContext.Connection.RemoteIpAddress?.ToString();
    }
}

/// <summary>
/// Request model for login.
/// </summary>
public class LoginRequest
{
    /// <summary>
    /// User's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// User's password.
    /// </summary>
    public string Password { get; set; } = string.Empty;

    /// <summary>
    /// Whether to extend the refresh token validity period.
    /// </summary>
    public bool RememberMe { get; set; }
}

/// <summary>
/// Request model for refresh token.
/// </summary>
public class RefreshTokenRequest
{
    /// <summary>
    /// The refresh token.
    /// </summary>
    public string RefreshToken { get; set; } = string.Empty;
}

/// <summary>
/// Request model for forgot password.
/// </summary>
public class ForgotPasswordRequest
{
    /// <summary>
    /// User's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;
}

/// <summary>
/// Request model for reset password.
/// </summary>
public class ResetPasswordRequest
{
    /// <summary>
    /// User's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Password reset token.
    /// </summary>
    public string Token { get; set; } = string.Empty;

    /// <summary>
    /// New password.
    /// </summary>
    public string NewPassword { get; set; } = string.Empty;

    /// <summary>
    /// Confirm new password.
    /// </summary>
    public string ConfirmPassword { get; set; } = string.Empty;
}
