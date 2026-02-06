using MediatR;

namespace Bayan.Application.Features.Auth.Commands.ForgotPassword;

/// <summary>
/// Command for requesting a password reset.
/// </summary>
public class ForgotPasswordCommand : IRequest<Unit>
{
    /// <summary>
    /// User's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Base URL for the password reset page.
    /// </summary>
    public string ResetUrl { get; set; } = string.Empty;
}
