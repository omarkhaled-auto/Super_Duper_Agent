using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Commands.RejectClarification;

/// <summary>
/// Command for rejecting a clarification with a reason.
/// </summary>
public class RejectClarificationCommand : IRequest<ClarificationDto>
{
    /// <summary>
    /// ID of the tender the clarification belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the clarification to reject.
    /// </summary>
    public Guid ClarificationId { get; set; }

    /// <summary>
    /// ID of the user rejecting the clarification.
    /// </summary>
    public Guid UserId { get; set; }

    /// <summary>
    /// Reason for rejection.
    /// </summary>
    public string Reason { get; set; } = string.Empty;
}
