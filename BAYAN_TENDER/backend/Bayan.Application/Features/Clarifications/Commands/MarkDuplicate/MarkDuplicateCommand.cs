using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Commands.MarkDuplicate;

/// <summary>
/// Command for marking a clarification as duplicate of another.
/// </summary>
public class MarkDuplicateCommand : IRequest<ClarificationDto>
{
    /// <summary>
    /// ID of the tender the clarification belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the clarification to mark as duplicate.
    /// </summary>
    public Guid ClarificationId { get; set; }

    /// <summary>
    /// ID of the original clarification this is a duplicate of.
    /// </summary>
    public Guid OriginalClarificationId { get; set; }

    /// <summary>
    /// ID of the user marking the duplicate.
    /// </summary>
    public Guid UserId { get; set; }
}
