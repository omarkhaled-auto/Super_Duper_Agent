using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Commands.DraftAnswer;

/// <summary>
/// Command for drafting an answer to a clarification.
/// </summary>
public class DraftAnswerCommand : IRequest<ClarificationDto>
{
    /// <summary>
    /// ID of the tender the clarification belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the clarification to answer.
    /// </summary>
    public Guid ClarificationId { get; set; }

    /// <summary>
    /// ID of the user drafting the answer.
    /// </summary>
    public Guid UserId { get; set; }

    /// <summary>
    /// The draft answer text.
    /// </summary>
    public string Answer { get; set; } = string.Empty;
}
