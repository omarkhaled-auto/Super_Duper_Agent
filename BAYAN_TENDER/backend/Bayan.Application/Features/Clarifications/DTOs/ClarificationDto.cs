using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for clarification summary information.
/// </summary>
public class ClarificationDto
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
    /// When the clarification was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }
}
