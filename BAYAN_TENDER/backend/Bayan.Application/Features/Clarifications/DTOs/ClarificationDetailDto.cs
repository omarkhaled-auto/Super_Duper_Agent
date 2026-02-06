using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for detailed clarification information including attachments and history.
/// </summary>
public class ClarificationDetailDto
{
    /// <summary>
    /// Unique identifier of the clarification.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// ID of the tender this clarification belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Title of the tender.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Reference number of the tender.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

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
    /// The answer to the question (if answered).
    /// </summary>
    public string? Answer { get; set; }

    /// <summary>
    /// Current status of the clarification.
    /// </summary>
    public ClarificationStatus Status { get; set; }

    /// <summary>
    /// Status display name.
    /// </summary>
    public string StatusName => Status.ToString();

    /// <summary>
    /// Type of clarification.
    /// </summary>
    public ClarificationType ClarificationType { get; set; }

    /// <summary>
    /// Type display name.
    /// </summary>
    public string TypeName => ClarificationType.ToString();

    /// <summary>
    /// Priority level.
    /// </summary>
    public ClarificationPriority Priority { get; set; }

    /// <summary>
    /// Priority display name.
    /// </summary>
    public string PriorityName => Priority.ToString();

    /// <summary>
    /// ID of the bidder who submitted the question (null if internal).
    /// </summary>
    public Guid? SubmittedByBidderId { get; set; }

    /// <summary>
    /// Name of the bidder who submitted the question.
    /// </summary>
    public string? BidderName { get; set; }

    /// <summary>
    /// Bidder contact person.
    /// </summary>
    public string? BidderContactPerson { get; set; }

    /// <summary>
    /// Bidder email.
    /// </summary>
    public string? BidderEmail { get; set; }

    /// <summary>
    /// ID of the user who submitted the question (for internal RFIs).
    /// </summary>
    public Guid? SubmittedByUserId { get; set; }

    /// <summary>
    /// Name of the user who submitted the question.
    /// </summary>
    public string? SubmittedByUserName { get; set; }

    /// <summary>
    /// Related BOQ section reference.
    /// </summary>
    public string? RelatedBoqSection { get; set; }

    /// <summary>
    /// Related document ID.
    /// </summary>
    public Guid? RelatedDocumentId { get; set; }

    /// <summary>
    /// Related document name.
    /// </summary>
    public string? RelatedDocumentName { get; set; }

    /// <summary>
    /// Whether the submitter identity should be hidden.
    /// </summary>
    public bool IsAnonymous { get; set; }

    /// <summary>
    /// When the question was submitted.
    /// </summary>
    public DateTime SubmittedAt { get; set; }

    /// <summary>
    /// When the question was answered.
    /// </summary>
    public DateTime? AnsweredAt { get; set; }

    /// <summary>
    /// ID of the user who answered the question.
    /// </summary>
    public Guid? AnsweredBy { get; set; }

    /// <summary>
    /// Name of the user who answered.
    /// </summary>
    public string? AnsweredByName { get; set; }

    /// <summary>
    /// ID of the user assigned to this clarification.
    /// </summary>
    public Guid? AssignedToId { get; set; }

    /// <summary>
    /// Name of the user assigned to this clarification.
    /// </summary>
    public string? AssignedToName { get; set; }

    /// <summary>
    /// If duplicate, reference to original clarification.
    /// </summary>
    public Guid? DuplicateOfId { get; set; }

    /// <summary>
    /// Reference number of the original clarification (if duplicate).
    /// </summary>
    public string? DuplicateOfReference { get; set; }

    /// <summary>
    /// Bulletin this was published in.
    /// </summary>
    public Guid? PublishedInBulletinId { get; set; }

    /// <summary>
    /// Bulletin number this was published in.
    /// </summary>
    public int? PublishedInBulletinNumber { get; set; }

    /// <summary>
    /// When this was published.
    /// </summary>
    public DateTime? PublishedAt { get; set; }

    /// <summary>
    /// Rejection reason (if rejected).
    /// </summary>
    public string? RejectionReason { get; set; }

    /// <summary>
    /// When the clarification was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }

    /// <summary>
    /// List of attachments associated with the clarification.
    /// </summary>
    public List<ClarificationAttachmentDto> Attachments { get; set; } = new();

    /// <summary>
    /// List of history entries for the clarification.
    /// </summary>
    public List<ClarificationHistoryDto> History { get; set; } = new();
}

/// <summary>
/// Data transfer object for clarification attachment.
/// </summary>
public class ClarificationAttachmentDto
{
    /// <summary>
    /// Unique identifier of the attachment.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSize { get; set; }

    /// <summary>
    /// MIME type of the file.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// When the attachment was uploaded.
    /// </summary>
    public DateTime UploadedAt { get; set; }
}

/// <summary>
/// Data transfer object for clarification history entry.
/// </summary>
public class ClarificationHistoryDto
{
    /// <summary>
    /// Unique identifier of the history entry.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Action performed.
    /// </summary>
    public string Action { get; set; } = string.Empty;

    /// <summary>
    /// Previous status (if applicable).
    /// </summary>
    public ClarificationStatus? FromStatus { get; set; }

    /// <summary>
    /// New status (if applicable).
    /// </summary>
    public ClarificationStatus? ToStatus { get; set; }

    /// <summary>
    /// Additional details about the action.
    /// </summary>
    public string? Details { get; set; }

    /// <summary>
    /// ID of the user who performed the action.
    /// </summary>
    public Guid PerformedById { get; set; }

    /// <summary>
    /// Name of the user who performed the action.
    /// </summary>
    public string PerformedByName { get; set; } = string.Empty;

    /// <summary>
    /// When the action was performed.
    /// </summary>
    public DateTime PerformedAt { get; set; }
}
