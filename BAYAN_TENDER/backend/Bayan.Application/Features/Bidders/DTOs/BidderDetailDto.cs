using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Bidders.DTOs;

/// <summary>
/// Data transfer object for bidder full details view.
/// </summary>
public class BidderDetailDto
{
    /// <summary>
    /// Unique identifier for the bidder.
    /// </summary>
    public Guid Id { get; set; }

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
    /// Path to company profile document in MinIO.
    /// </summary>
    public string? CompanyProfilePath { get; set; }

    /// <summary>
    /// Whether the bidder is active.
    /// </summary>
    public bool IsActive { get; set; }

    /// <summary>
    /// Last login timestamp.
    /// </summary>
    public DateTime? LastLoginAt { get; set; }

    /// <summary>
    /// Timestamp when the bidder was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }

    /// <summary>
    /// Timestamp when the bidder was last updated.
    /// </summary>
    public DateTime? UpdatedAt { get; set; }

    /// <summary>
    /// Number of tenders this bidder is invited to.
    /// </summary>
    public int TenderCount { get; set; }
}
