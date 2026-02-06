using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Commands.SubmitClarification;

/// <summary>
/// Command for submitting a new clarification question from a bidder.
/// </summary>
public class SubmitClarificationCommand : IRequest<ClarificationDto>
{
    /// <summary>
    /// ID of the tender to submit the clarification for.
    /// </summary>
    public Guid TenderId { get; set; }

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
