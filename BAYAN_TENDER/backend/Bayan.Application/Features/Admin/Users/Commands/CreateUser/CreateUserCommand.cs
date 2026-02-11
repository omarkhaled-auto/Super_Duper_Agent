using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Admin.Users.Commands.CreateUser;

/// <summary>
/// Command to create a new user.
/// </summary>
public record CreateUserCommand : IRequest<CreateUserResult>
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
    /// Whether to send an invitation email with the temporary password.
    /// </summary>
    public bool SendInvitationEmail { get; init; } = true;

    /// <summary>
    /// Optional admin-provided password. If set, uses this instead of generating a temporary password.
    /// </summary>
    public string? Password { get; init; }
}

/// <summary>
/// Result of CreateUserCommand execution.
/// </summary>
public record CreateUserResult
{
    /// <summary>
    /// The ID of the created user.
    /// </summary>
    public Guid UserId { get; init; }

    /// <summary>
    /// The temporary password generated for the user (only returned if email was not sent).
    /// </summary>
    public string? TemporaryPassword { get; init; }

    /// <summary>
    /// Indicates whether the invitation email was sent successfully.
    /// </summary>
    public bool InvitationEmailSent { get; init; }
}
