namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for drafting an answer to a clarification.
/// </summary>
public class DraftAnswerDto
{
    /// <summary>
    /// The draft answer text.
    /// </summary>
    public string Answer { get; set; } = string.Empty;
}
