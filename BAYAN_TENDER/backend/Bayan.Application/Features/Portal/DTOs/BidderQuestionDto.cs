namespace Bayan.Application.Features.Portal.DTOs;

/// <summary>
/// Data transfer object for a bidder-submitted question.
/// </summary>
public class BidderQuestionDto
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
    /// Subject of the question.
    /// </summary>
    public string Subject { get; set; } = string.Empty;

    /// <summary>
    /// The question content.
    /// </summary>
    public string Question { get; set; } = string.Empty;

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
    /// Current status display.
    /// </summary>
    public string StatusDisplay { get; set; } = string.Empty;
}
