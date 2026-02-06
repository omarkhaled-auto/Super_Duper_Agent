namespace Bayan.Application.Features.Portal.DTOs;

/// <summary>
/// Data transfer object for bidder login response.
/// </summary>
public class BidderLoginResponseDto
{
    /// <summary>
    /// The authenticated bidder's information.
    /// </summary>
    public BidderInfoDto Bidder { get; set; } = null!;

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

/// <summary>
/// Data transfer object for bidder information.
/// </summary>
public class BidderInfoDto
{
    /// <summary>
    /// Bidder unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Contact person name.
    /// </summary>
    public string ContactPerson { get; set; } = string.Empty;

    /// <summary>
    /// Contact email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Contact phone number.
    /// </summary>
    public string? Phone { get; set; }

    /// <summary>
    /// Trade specialization/category.
    /// </summary>
    public string? TradeSpecialization { get; set; }

    /// <summary>
    /// List of tenders the bidder has access to.
    /// </summary>
    public List<BidderTenderAccessDto> TenderAccess { get; set; } = new();
}

/// <summary>
/// Data transfer object for bidder's tender access information.
/// </summary>
public class BidderTenderAccessDto
{
    /// <summary>
    /// Tender unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Tender reference number.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Qualification status for this tender.
    /// </summary>
    public string QualificationStatus { get; set; } = string.Empty;
}
