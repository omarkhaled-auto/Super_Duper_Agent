using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Commands.SubmitInternalRfi;

/// <summary>
/// Command for submitting an internal RFI from the tender team.
/// </summary>
public class SubmitInternalRfiCommand : IRequest<ClarificationDto>
{
    /// <summary>
    /// ID of the tender to submit the RFI for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the user submitting the RFI.
    /// </summary>
    public Guid UserId { get; set; }

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
