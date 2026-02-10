using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents the relationship between a tender and a bidder.
/// </summary>
public class TenderBidder : BaseEntity
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// When the invitation was sent.
    /// </summary>
    public DateTime? InvitationSentAt { get; set; }

    /// <summary>
    /// When the invitation was opened/viewed.
    /// </summary>
    public DateTime? InvitationOpenedAt { get; set; }

    /// <summary>
    /// When the bidder registered for this tender.
    /// </summary>
    public DateTime? RegisteredAt { get; set; }

    /// <summary>
    /// NDA signing status.
    /// </summary>
    public NdaStatus NdaStatus { get; set; } = NdaStatus.Pending;

    /// <summary>
    /// Path to NDA document in MinIO.
    /// </summary>
    public string? NdaDocumentPath { get; set; }

    /// <summary>
    /// Date NDA was signed.
    /// </summary>
    public DateTime? NdaSignedDate { get; set; }

    /// <summary>
    /// Date NDA expires.
    /// </summary>
    public DateTime? NdaExpiryDate { get; set; }

    /// <summary>
    /// Qualification status for this tender.
    /// </summary>
    public QualificationStatus QualificationStatus { get; set; } = QualificationStatus.Pending;

    /// <summary>
    /// When the bidder was qualified.
    /// </summary>
    public DateTime? QualifiedAt { get; set; }

    /// <summary>
    /// Reason for the qualification decision.
    /// </summary>
    public string? QualificationReason { get; set; }

    // Navigation properties
    /// <summary>
    /// The tender.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// The bidder.
    /// </summary>
    public virtual Bidder Bidder { get; set; } = null!;
}
