namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for marking a clarification as duplicate.
/// </summary>
public class MarkDuplicateDto
{
    /// <summary>
    /// ID of the original clarification this is a duplicate of.
    /// </summary>
    public Guid OriginalClarificationId { get; set; }
}
