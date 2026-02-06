using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Clarifications;

/// <summary>
/// Command to submit a bidder question (clarification request).
/// </summary>
public class SubmitBidderQuestionCommand : IRequest<BidderQuestionDto>
{
    /// <summary>
    /// Tender unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder ID submitting the question.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Subject of the question.
    /// </summary>
    public string Subject { get; set; } = string.Empty;

    /// <summary>
    /// The question content.
    /// </summary>
    public string Question { get; set; } = string.Empty;

    /// <summary>
    /// Related BOQ section reference (optional).
    /// </summary>
    public string? RelatedBoqSection { get; set; }

    /// <summary>
    /// Whether the submitter identity should be hidden.
    /// </summary>
    public bool IsAnonymous { get; set; }
}
