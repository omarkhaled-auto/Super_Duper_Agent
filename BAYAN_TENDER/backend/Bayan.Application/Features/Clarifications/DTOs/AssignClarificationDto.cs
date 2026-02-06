namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for assigning a clarification to a team member.
/// </summary>
public class AssignClarificationDto
{
    /// <summary>
    /// ID of the user to assign the clarification to.
    /// </summary>
    public Guid AssignToUserId { get; set; }
}
