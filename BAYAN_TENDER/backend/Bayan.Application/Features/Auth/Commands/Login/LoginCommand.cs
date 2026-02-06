using Bayan.Application.Features.Auth.DTOs;
using MediatR;

namespace Bayan.Application.Features.Auth.Commands.Login;

/// <summary>
/// Command for user login.
/// </summary>
public class LoginCommand : IRequest<LoginResponseDto>
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

    /// <summary>
    /// IP address of the requesting client (set by the handler).
    /// </summary>
    public string? IpAddress { get; set; }
}
