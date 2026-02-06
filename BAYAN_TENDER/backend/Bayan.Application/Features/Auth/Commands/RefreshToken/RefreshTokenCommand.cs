using Bayan.Application.Features.Auth.DTOs;
using MediatR;

namespace Bayan.Application.Features.Auth.Commands.RefreshToken;

/// <summary>
/// Command for refreshing JWT tokens.
/// </summary>
public class RefreshTokenCommand : IRequest<TokenDto>
{
    /// <summary>
    /// The current refresh token.
    /// </summary>
    public string RefreshToken { get; set; } = string.Empty;

    /// <summary>
    /// IP address of the requesting client (set by the handler).
    /// </summary>
    public string? IpAddress { get; set; }
}
