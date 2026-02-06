using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a bidder (company that participates in tenders).
/// </summary>
public class Bidder : BaseEntity
{
    /// <summary>
    /// Company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Commercial Registration Number (unique identifier for business registration).
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
    public PrequalificationStatus PrequalificationStatus { get; set; } = PrequalificationStatus.Pending;

    /// <summary>
    /// Path to company profile document in MinIO.
    /// </summary>
    public string? CompanyProfilePath { get; set; }

    /// <summary>
    /// Whether the bidder is active.
    /// </summary>
    public bool IsActive { get; set; } = true;

    /// <summary>
    /// Password hash for bidder portal login.
    /// </summary>
    public string? PasswordHash { get; set; }

    /// <summary>
    /// Last login timestamp.
    /// </summary>
    public DateTime? LastLoginAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tenders this bidder is invited to.
    /// </summary>
    public virtual ICollection<TenderBidder> TenderBidders { get; set; } = new List<TenderBidder>();

    /// <summary>
    /// Clarifications submitted by this bidder.
    /// </summary>
    public virtual ICollection<Clarification> Clarifications { get; set; } = new List<Clarification>();

    /// <summary>
    /// Addendum acknowledgments by this bidder.
    /// </summary>
    public virtual ICollection<AddendumAcknowledgment> AddendumAcknowledgments { get; set; } = new List<AddendumAcknowledgment>();

    /// <summary>
    /// Bid submissions by this bidder.
    /// </summary>
    public virtual ICollection<BidSubmission> BidSubmissions { get; set; } = new List<BidSubmission>();

    /// <summary>
    /// Technical scores for this bidder.
    /// </summary>
    public virtual ICollection<TechnicalScore> TechnicalScores { get; set; } = new List<TechnicalScore>();

    /// <summary>
    /// Commercial scores for this bidder.
    /// </summary>
    public virtual ICollection<CommercialScore> CommercialScores { get; set; } = new List<CommercialScore>();

    /// <summary>
    /// Combined scorecards for this bidder.
    /// </summary>
    public virtual ICollection<CombinedScorecard> CombinedScorecards { get; set; } = new List<CombinedScorecard>();

    /// <summary>
    /// Bid exceptions for this bidder.
    /// </summary>
    public virtual ICollection<BidException> BidExceptions { get; set; } = new List<BidException>();

    /// <summary>
    /// Vendor pricing snapshots for this bidder.
    /// </summary>
    public virtual ICollection<VendorPricingSnapshot> VendorPricingSnapshots { get; set; } = new List<VendorPricingSnapshot>();
}
