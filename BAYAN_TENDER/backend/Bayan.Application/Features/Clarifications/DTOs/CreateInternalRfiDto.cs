using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for creating an internal RFI.
/// </summary>
public class CreateInternalRfiDto
{
    /// <summary>
    /// Subject of the RFI.
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
    /// Priority level.
    /// </summary>
    public ClarificationPriority Priority { get; set; } = ClarificationPriority.Normal;

    /// <summary>
    /// List of attachment file IDs to associate with the RFI.
    /// </summary>
    public List<Guid> AttachmentIds { get; set; } = new();
}
