using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Commands.ApproveAnswer;

/// <summary>
/// Command for approving a drafted answer, changing status to Answered.
/// </summary>
public class ApproveAnswerCommand : IRequest<ClarificationDto>
{
    /// <summary>
    /// ID of the tender the clarification belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the clarification to approve the answer for.
    /// </summary>
    public Guid ClarificationId { get; set; }

    /// <summary>
    /// ID of the user approving the answer.
    /// </summary>
    public Guid UserId { get; set; }

    public ApproveAnswerCommand()
    {
    }

    public ApproveAnswerCommand(Guid tenderId, Guid clarificationId, Guid userId)
    {
        TenderId = tenderId;
        ClarificationId = clarificationId;
        UserId = userId;
    }
}
