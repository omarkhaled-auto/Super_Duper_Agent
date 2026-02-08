using MediatR;

namespace Bayan.Application.Features.Portal.Auth;

/// <summary>
/// Command for activating a bidder account by setting a password.
/// </summary>
public class ActivateBidderAccountCommand : IRequest<Unit>
{
    /// <summary>
    /// Bidder's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// The activation token sent via email.
    /// </summary>
    public string ActivationToken { get; set; } = string.Empty;

    /// <summary>
    /// The new password.
    /// </summary>
    public string Password { get; set; } = string.Empty;

    /// <summary>
    /// Confirmation of the new password.
    /// </summary>
    public string ConfirmPassword { get; set; } = string.Empty;
}
