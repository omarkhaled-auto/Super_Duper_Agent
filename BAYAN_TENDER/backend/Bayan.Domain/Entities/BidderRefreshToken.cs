using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a refresh token for bidder portal JWT authentication.
/// </summary>
public class BidderRefreshToken : BaseEntity
{
    /// <summary>
    /// The refresh token value.
    /// </summary>
    public string Token { get; set; } = string.Empty;

    /// <summary>
    /// Token expiration date.
    /// </summary>
    public DateTime ExpiresAt { get; set; }

    /// <summary>
    /// Whether the token has been revoked.
    /// </summary>
    public bool IsRevoked { get; set; }

    /// <summary>
    /// Date when the token was revoked (if applicable).
    /// </summary>
    public DateTime? RevokedAt { get; set; }

    /// <summary>
    /// IP address from which the token was created.
    /// </summary>
    public string? CreatedByIp { get; set; }

    /// <summary>
    /// IP address from which the token was revoked (if applicable).
    /// </summary>
    public string? RevokedByIp { get; set; }

    /// <summary>
    /// The token that replaced this one (if rotated).
    /// </summary>
    public string? ReplacedByToken { get; set; }

    /// <summary>
    /// Foreign key to the bidder.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Navigation property to the bidder.
    /// </summary>
    public Bidder Bidder { get; set; } = null!;

    /// <summary>
    /// Whether the token is currently active (not expired and not revoked).
    /// </summary>
    public bool IsActive => !IsRevoked && DateTime.UtcNow < ExpiresAt;

    /// <summary>
    /// Whether the token has expired.
    /// </summary>
    public bool IsExpired => DateTime.UtcNow >= ExpiresAt;
}
