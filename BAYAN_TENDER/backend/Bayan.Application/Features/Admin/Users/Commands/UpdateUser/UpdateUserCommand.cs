using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Admin.Users.Commands.UpdateUser;

/// <summary>
/// Command to update an existing user.
/// </summary>
public record UpdateUserCommand : IRequest<bool>
{
    /// <summary>
    /// The ID of the user to update.
    /// </summary>
    public Guid Id { get; init; }

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
