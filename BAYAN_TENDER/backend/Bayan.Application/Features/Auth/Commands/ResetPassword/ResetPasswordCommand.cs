using MediatR;

namespace Bayan.Application.Features.Auth.Commands.ResetPassword;

/// <summary>
/// Command for resetting password with a reset token.
/// </summary>
public class ResetPasswordCommand : IRequest<Unit>
{
    /// <summary>
    /// User's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// The password reset token.
    /// </summary>
    public string Token { get; set; } = string.Empty;

    /// <summary>
    /// The new password.
    /// </summary>
    public string NewPassword { get; set; } = string.Empty;

    /// <summary>
    /// Confirmation of the new password.
    /// </summary>
    public string ConfirmPassword { get; set; } = string.Empty;
}
