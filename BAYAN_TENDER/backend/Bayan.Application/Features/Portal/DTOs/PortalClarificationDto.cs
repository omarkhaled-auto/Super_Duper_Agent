using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Portal.DTOs;

/// <summary>
/// Data transfer object for clarifications displayed in the bidder portal.
/// </summary>
public class PortalClarificationDto
{
    /// <summary>
    /// Clarification unique identifier.
    /// </summary>
    public Guid Id { get; set; }

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
    /// The answer to the question.
    /// </summary>
    public string? Answer { get; set; }

    /// <summary>
    /// Related BOQ section reference.
    /// </summary>
    public string? RelatedBoqSection { get; set; }

    /// <summary>
    /// When the question was submitted.
    /// </summary>
    public DateTime SubmittedAt { get; set; }

    /// <summary>
    /// When the question was answered.
    /// </summary>
    public DateTime? AnsweredAt { get; set; }

    /// <summary>
    /// When this was published.
    /// </summary>
    public DateTime? PublishedAt { get; set; }

    /// <summary>
    /// Type of clarification.
    /// </summary>
    public ClarificationType ClarificationType { get; set; }

    /// <summary>
    /// Priority level.
    /// </summary>
    public ClarificationPriority Priority { get; set; }

    /// <summary>
    /// Current status.
    /// </summary>
    public ClarificationStatus Status { get; set; }
}
