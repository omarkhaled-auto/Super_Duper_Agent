using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a clarification/RFI for a tender.
/// </summary>
public class Clarification : BaseEntity
{
    /// <summary>
    /// Tender this clarification belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Reference number (e.g., CL-001).
    /// </summary>
    public string ReferenceNumber { get; set; } = string.Empty;

    /// <summary>
    /// Subject of the clarification.
    /// </summary>
    public string Subject { get; set; } = string.Empty;

    /// <summary>
    /// The question being asked.
    /// </summary>
    public string Question { get; set; } = string.Empty;

    /// <summary>
    /// Bidder who submitted the question (null if internal).
    /// </summary>
    public Guid? SubmittedByBidderId { get; set; }

    /// <summary>
    /// User who submitted the question (null if from bidder).
    /// </summary>
    public Guid? SubmittedByUserId { get; set; }

    /// <summary>
    /// Related BOQ section reference.
    /// </summary>
    public string? RelatedBoqSection { get; set; }

    /// <summary>
    /// Related document ID.
    /// </summary>
    public Guid? RelatedDocumentId { get; set; }

    /// <summary>
    /// Whether the submitter identity should be hidden.
    /// </summary>
    public bool IsAnonymous { get; set; }

    /// <summary>
    /// Priority level.
    /// </summary>
    public ClarificationPriority Priority { get; set; } = ClarificationPriority.Normal;

    /// <summary>
    /// The answer to the question.
    /// </summary>
    public string? Answer { get; set; }

    /// <summary>
    /// User who answered the question.
    /// </summary>
    public Guid? AnsweredBy { get; set; }

    /// <summary>
    /// When the question was answered.
    /// </summary>
    public DateTime? AnsweredAt { get; set; }

    /// <summary>
    /// User this clarification is assigned to.
    /// </summary>
    public Guid? AssignedToId { get; set; }

    /// <summary>
    /// Type of clarification.
    /// </summary>
    public ClarificationType ClarificationType { get; set; } = ClarificationType.BidderQuestion;

    /// <summary>
    /// Current status.
    /// </summary>
    public ClarificationStatus Status { get; set; } = ClarificationStatus.Submitted;

    /// <summary>
    /// If duplicate, reference to original clarification.
    /// </summary>
    public Guid? DuplicateOfId { get; set; }

    /// <summary>
    /// Bulletin this was published in.
    /// </summary>
    public Guid? PublishedInBulletinId { get; set; }

    /// <summary>
    /// When this was published.
    /// </summary>
    public DateTime? PublishedAt { get; set; }

    /// <summary>
    /// When the question was submitted.
    /// </summary>
    public DateTime SubmittedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this clarification.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Bidder who submitted the question.
    /// </summary>
    public virtual Bidder? SubmittedByBidder { get; set; }

    /// <summary>
    /// User who submitted the question.
    /// </summary>
    public virtual User? SubmittedByUser { get; set; }

    /// <summary>
    /// Related document.
    /// </summary>
    public virtual Document? RelatedDocument { get; set; }

    /// <summary>
    /// User who answered.
    /// </summary>
    public virtual User? Answerer { get; set; }

    /// <summary>
    /// User this clarification is assigned to.
    /// </summary>
    public virtual User? AssignedTo { get; set; }

    /// <summary>
    /// Original clarification if this is a duplicate.
    /// </summary>
    public virtual Clarification? DuplicateOf { get; set; }

    /// <summary>
    /// Duplicates of this clarification.
    /// </summary>
    public virtual ICollection<Clarification> Duplicates { get; set; } = new List<Clarification>();

    /// <summary>
    /// Bulletin this was published in.
    /// </summary>
    public virtual ClarificationBulletin? PublishedInBulletin { get; set; }

    /// <summary>
    /// File attachments associated with this clarification.
    /// </summary>
    public virtual ICollection<ClarificationAttachment> Attachments { get; set; } = new List<ClarificationAttachment>();
}
