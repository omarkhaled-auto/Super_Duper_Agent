using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Tenders.DTOs;

/// <summary>
/// Data transfer object for tender bidder relationship.
/// </summary>
public class TenderBidderDto
{
    /// <summary>
    /// Unique identifier for the tender-bidder relationship.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Company name of the bidder.
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
    /// When the invitation was sent.
    /// </summary>
    public DateTime? InvitationSentAt { get; set; }

    /// <summary>
    /// When the bidder registered for this tender.
    /// </summary>
    public DateTime? RegisteredAt { get; set; }

    /// <summary>
    /// NDA signing status.
    /// </summary>
    public NdaStatus NdaStatus { get; set; }

    /// <summary>
    /// Qualification status for this tender.
    /// </summary>
    public QualificationStatus QualificationStatus { get; set; }
}
