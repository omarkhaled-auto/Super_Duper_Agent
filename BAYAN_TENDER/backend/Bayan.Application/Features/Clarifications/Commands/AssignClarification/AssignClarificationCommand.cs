using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Commands.AssignClarification;

/// <summary>
/// Command for assigning a clarification to a team member.
/// </summary>
public class AssignClarificationCommand : IRequest<ClarificationDto>
{
    /// <summary>
    /// ID of the tender the clarification belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the clarification to assign.
    /// </summary>
    public Guid ClarificationId { get; set; }

    /// <summary>
    /// ID of the user to assign the clarification to.
    /// </summary>
    public Guid AssignToUserId { get; set; }

    /// <summary>
    /// ID of the user performing the assignment.
    /// </summary>
    public Guid AssignedByUserId { get; set; }
}
