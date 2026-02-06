using Bayan.Domain.Entities;

namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for JWT token generation and validation operations.
/// </summary>
public interface IJwtTokenService
{
    /// <summary>
    /// Generates an access token for the specified user.
    /// </summary>
    /// <param name="user">The user to generate the token for.</param>
    /// <returns>The generated JWT access token.</returns>
    string GenerateAccessToken(User user);

    /// <summary>
    /// Generates an access token for a bidder.
    /// </summary>
    /// <param name="bidder">The bidder to generate the token for.</param>
    /// <returns>The generated JWT access token.</returns>
    string GenerateBidderAccessToken(Bidder bidder);

    /// <summary>
    /// Generates a refresh token.
    /// </summary>
    /// <returns>A new refresh token string.</returns>
    string GenerateRefreshToken();

    /// <summary>
    /// Validates a JWT access token and extracts the user ID.
    /// </summary>
    /// <param name="token">The token to validate.</param>
    /// <returns>The user ID if valid; otherwise, null.</returns>
    Guid? ValidateAccessToken(string token);

    /// <summary>
    /// Validates a JWT access token and extracts the bidder ID.
    /// </summary>
    /// <param name="token">The token to validate.</param>
    /// <returns>The bidder ID if valid and is a bidder token; otherwise, null.</returns>
    Guid? ValidateBidderAccessToken(string token);

    /// <summary>
    /// Gets the access token expiration time in minutes.
    /// </summary>
    int AccessTokenExpirationMinutes { get; }

    /// <summary>
    /// Gets the refresh token expiration time in days.
    /// </summary>
    int RefreshTokenExpirationDays { get; }
}
