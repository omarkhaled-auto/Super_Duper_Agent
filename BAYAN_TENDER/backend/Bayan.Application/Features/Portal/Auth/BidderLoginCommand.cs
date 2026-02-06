using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Auth;

/// <summary>
/// Command for bidder portal login.
/// </summary>
public class BidderLoginCommand : IRequest<BidderLoginResponseDto>
{
    /// <summary>
    /// Bidder's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Bidder's password.
    /// </summary>
    public string Password { get; set; } = string.Empty;

    /// <summary>
    /// Optional tender ID to validate access to.
    /// </summary>
    public Guid? TenderId { get; set; }

    /// <summary>
    /// Whether to extend the refresh token validity period.
    /// </summary>
    public bool RememberMe { get; set; }

    /// <summary>
    /// IP address of the requesting client (set by the handler).
    /// </summary>
    public string? IpAddress { get; set; }
}
