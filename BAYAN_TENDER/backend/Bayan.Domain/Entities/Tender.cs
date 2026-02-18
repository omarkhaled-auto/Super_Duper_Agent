using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a tender in the system.
/// </summary>
public class Tender : BaseEntity, IAuditableEntity
{
    /// <summary>
    /// Tender title.
    /// </summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Unique tender reference number.
    /// </summary>
    public string Reference { get; set; } = string.Empty;

    /// <summary>
    /// Tender description.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Client issuing the tender.
    /// </summary>
    public Guid ClientId { get; set; }

    /// <summary>
    /// Type of tender procedure.
    /// </summary>
    public TenderType TenderType { get; set; }

    /// <summary>
    /// Base currency for the tender (ISO 4217 code).
    /// </summary>
    public string BaseCurrency { get; set; } = "AED";

    /// <summary>
    /// Estimated value of the tender.
    /// </summary>
    public decimal? EstimatedValue { get; set; }

    /// <summary>
    /// Number of days the bid is valid.
    /// </summary>
    public int BidValidityDays { get; set; } = 90;

    /// <summary>
    /// Date the tender was issued.
    /// </summary>
    public DateTime IssueDate { get; set; }

    /// <summary>
    /// Deadline for clarification questions.
    /// </summary>
    public DateTime ClarificationDeadline { get; set; }

    /// <summary>
    /// Deadline for bid submissions.
    /// </summary>
    public DateTime SubmissionDeadline { get; set; }

    /// <summary>
    /// Date when bids will be opened.
    /// </summary>
    public DateTime OpeningDate { get; set; }

    /// <summary>
    /// Weight for technical evaluation (percentage).
    /// </summary>
    public int TechnicalWeight { get; set; } = 40;

    /// <summary>
    /// Weight for commercial evaluation (percentage).
    /// </summary>
    public int CommercialWeight { get; set; } = 60;

    /// <summary>
    /// Pricing level for the BOQ hierarchy.
    /// Determines at which level bidders must provide prices.
    /// </summary>
    public PricingLevel PricingLevel { get; set; } = PricingLevel.SubItem;

    /// <summary>
    /// Current status of the tender.
    /// </summary>
    public TenderStatus Status { get; set; } = TenderStatus.Draft;

    /// <summary>
    /// When the tender was published.
    /// </summary>
    public DateTime? PublishedAt { get; set; }

    /// <summary>
    /// When the tender was awarded.
    /// </summary>
    public DateTime? AwardedAt { get; set; }

    // IAuditableEntity implementation
    /// <summary>
    /// User who created the tender.
    /// </summary>
    public Guid? CreatedBy { get; set; }

    /// <summary>
    /// User who last modified the tender.
    /// </summary>
    public Guid? LastModifiedBy { get; set; }

    /// <summary>
    /// When the tender was last modified.
    /// </summary>
    public DateTime? LastModifiedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Client associated with this tender.
    /// </summary>
    public virtual Client Client { get; set; } = null!;

    /// <summary>
    /// User who created the tender.
    /// </summary>
    public virtual User Creator { get; set; } = null!;

    /// <summary>
    /// Evaluation criteria for this tender.
    /// </summary>
    public virtual ICollection<EvaluationCriteria> EvaluationCriteria { get; set; } = new List<EvaluationCriteria>();

    /// <summary>
    /// Bidders invited to this tender.
    /// </summary>
    public virtual ICollection<TenderBidder> TenderBidders { get; set; } = new List<TenderBidder>();

    /// <summary>
    /// Documents associated with this tender.
    /// </summary>
    public virtual ICollection<Document> Documents { get; set; } = new List<Document>();

    /// <summary>
    /// Addenda for this tender.
    /// </summary>
    public virtual ICollection<Addendum> Addenda { get; set; } = new List<Addendum>();

    /// <summary>
    /// Clarifications for this tender.
    /// </summary>
    public virtual ICollection<Clarification> Clarifications { get; set; } = new List<Clarification>();

    /// <summary>
    /// Clarification bulletins for this tender.
    /// </summary>
    public virtual ICollection<ClarificationBulletin> ClarificationBulletins { get; set; } = new List<ClarificationBulletin>();

    /// <summary>
    /// BOQ sections for this tender.
    /// </summary>
    public virtual ICollection<BoqSection> BoqSections { get; set; } = new List<BoqSection>();

    /// <summary>
    /// BOQ items for this tender.
    /// </summary>
    public virtual ICollection<BoqItem> BoqItems { get; set; } = new List<BoqItem>();

    /// <summary>
    /// Bid submissions for this tender.
    /// </summary>
    public virtual ICollection<BidSubmission> BidSubmissions { get; set; } = new List<BidSubmission>();

    /// <summary>
    /// Evaluation panel members for this tender.
    /// </summary>
    public virtual ICollection<EvaluationPanel> EvaluationPanels { get; set; } = new List<EvaluationPanel>();

    /// <summary>
    /// Technical scores for this tender.
    /// </summary>
    public virtual ICollection<TechnicalScore> TechnicalScores { get; set; } = new List<TechnicalScore>();

    /// <summary>
    /// Evaluation state for this tender.
    /// </summary>
    public virtual EvaluationState? EvaluationState { get; set; }

    /// <summary>
    /// Commercial scores for this tender.
    /// </summary>
    public virtual ICollection<CommercialScore> CommercialScores { get; set; } = new List<CommercialScore>();

    /// <summary>
    /// Combined scorecards for this tender.
    /// </summary>
    public virtual ICollection<CombinedScorecard> CombinedScorecards { get; set; } = new List<CombinedScorecard>();

    /// <summary>
    /// Bid exceptions for this tender.
    /// </summary>
    public virtual ICollection<BidException> BidExceptions { get; set; } = new List<BidException>();

    /// <summary>
    /// Approval workflow for this tender.
    /// </summary>
    public virtual ApprovalWorkflow? ApprovalWorkflow { get; set; }

    /// <summary>
    /// Vendor pricing snapshots for this tender.
    /// </summary>
    public virtual ICollection<VendorPricingSnapshot> VendorPricingSnapshots { get; set; } = new List<VendorPricingSnapshot>();

    /// <summary>
    /// Email logs for this tender.
    /// </summary>
    public virtual ICollection<EmailLog> EmailLogs { get; set; } = new List<EmailLog>();
}
