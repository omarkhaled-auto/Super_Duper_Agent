using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Bidders.DTOs;

/// <summary>
/// Data transfer object for updating an existing bidder.
/// </summary>
public class UpdateBidderDto
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

    /// <summary>
    /// Prequalification status.
    /// </summary>
    public PrequalificationStatus PrequalificationStatus { get; set; }

    /// <summary>
    /// Whether the bidder is active.
    /// </summary>
    public bool IsActive { get; set; } = true;
}
