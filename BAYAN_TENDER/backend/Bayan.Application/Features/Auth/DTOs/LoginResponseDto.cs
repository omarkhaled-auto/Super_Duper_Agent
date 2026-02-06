namespace Bayan.Application.Features.Auth.DTOs;

/// <summary>
/// Data transfer object for login response.
/// </summary>
public class LoginResponseDto
{
    /// <summary>
    /// The authenticated user's information.
    /// </summary>
    public UserDto User { get; set; } = null!;

    /// <summary>
    /// JWT access token.
    /// </summary>
    public string AccessToken { get; set; } = string.Empty;

    /// <summary>
    /// Refresh token for obtaining new access tokens.
    /// </summary>
    public string RefreshToken { get; set; } = string.Empty;

    /// <summary>
    /// Access token expiration time in UTC.
    /// </summary>
    public DateTime AccessTokenExpiresAt { get; set; }

    /// <summary>
    /// Refresh token expiration time in UTC.
    /// </summary>
    public DateTime RefreshTokenExpiresAt { get; set; }

    /// <summary>
    /// Token type (always "Bearer").
    /// </summary>
    public string TokenType { get; set; } = "Bearer";
}
