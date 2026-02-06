namespace Bayan.Application.Features.Bidders.DTOs;

/// <summary>
/// Data transfer object for creating a new bidder.
/// </summary>
public class CreateBidderDto
{
    /// <summary>
    /// Company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Commercial Registration Number.
    /// </summary>
    public string? CRNumber { get; set; }

    /// <summary>
    /// Trade license number.
    /// </summary>
    public string? LicenseNumber { get; set; }

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
}
