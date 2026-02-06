namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for creating a new clarification (bidder question).
/// </summary>
public class CreateClarificationDto
{
    /// <summary>
    /// Subject of the clarification.
    /// </summary>
    public string Subject { get; set; } = string.Empty;

    /// <summary>
    /// The question being asked.
    /// </summary>
    public string Question { get; set; } = string.Empty;

    /// <summary>
    /// Related BOQ section reference.
    /// </summary>
    public string? RelatedBoqSection { get; set; }

    /// <summary>
    /// Related document ID.
    /// </summary>
    public Guid? RelatedDocumentId { get; set; }

    /// <summary>
    /// ID of the bidder submitting the question.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// List of attachment file IDs to associate with the clarification.
    /// </summary>
    public List<Guid> AttachmentIds { get; set; } = new();

    /// <summary>
    /// Whether the submitter identity should be hidden.
    /// </summary>
    public bool IsAnonymous { get; set; }
}
