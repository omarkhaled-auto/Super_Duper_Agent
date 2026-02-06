using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Auth.DTOs;

/// <summary>
/// Data transfer object for user information.
/// </summary>
public class UserDto
{
    /// <summary>
    /// User's unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// User's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// User's first name.
    /// </summary>
    public string FirstName { get; set; } = string.Empty;

    /// <summary>
    /// User's last name.
    /// </summary>
    public string LastName { get; set; } = string.Empty;

    /// <summary>
    /// User's full name.
    /// </summary>
    public string FullName { get; set; } = string.Empty;

    /// <summary>
    /// User's phone number.
    /// </summary>
    public string? PhoneNumber { get; set; }

    /// <summary>
    /// User's role in the system.
    /// </summary>
    public UserRole Role { get; set; }

    /// <summary>
    /// Role name for display purposes.
    /// </summary>
    public string RoleName => Role.ToString();

    /// <summary>
    /// Whether the user account is active.
    /// </summary>
    public bool IsActive { get; set; }

    /// <summary>
    /// Whether the user's email has been verified.
    /// </summary>
    public bool EmailVerified { get; set; }

    /// <summary>
    /// Company name (for bidder users).
    /// </summary>
    public string? CompanyName { get; set; }

    /// <summary>
    /// Department or organizational unit.
    /// </summary>
    public string? Department { get; set; }

    /// <summary>
    /// Job title or position.
    /// </summary>
    public string? JobTitle { get; set; }

    /// <summary>
    /// User's profile picture URL.
    /// </summary>
    public string? ProfilePictureUrl { get; set; }

    /// <summary>
    /// User's preferred language.
    /// </summary>
    public string PreferredLanguage { get; set; } = "ar";

    /// <summary>
    /// User's timezone.
    /// </summary>
    public string TimeZone { get; set; } = "Asia/Riyadh";

    /// <summary>
    /// Last login timestamp.
    /// </summary>
    public DateTime? LastLoginAt { get; set; }

    /// <summary>
    /// Account creation timestamp.
    /// </summary>
    public DateTime CreatedAt { get; set; }
}
