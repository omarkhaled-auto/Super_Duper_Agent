using Bayan.Application.Features.Auth.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Auth;

/// <summary>
/// Command for refreshing bidder portal JWT tokens.
/// </summary>
public class BidderRefreshTokenCommand : IRequest<TokenDto>
{
    /// <summary>
    /// The refresh token to exchange for new tokens.
    /// </summary>
    public string RefreshToken { get; set; } = string.Empty;

    /// <summary>
    /// IP address of the requesting client.
    /// </summary>
    public string? IpAddress { get; set; }
}
