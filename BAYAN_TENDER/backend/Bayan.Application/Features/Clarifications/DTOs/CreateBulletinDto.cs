namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for creating a clarification bulletin.
/// </summary>
public class CreateBulletinDto
{
    /// <summary>
    /// IDs of clarifications to include in the bulletin.
    /// </summary>
    public List<Guid> ClarificationIds { get; set; } = new();

    /// <summary>
    /// Optional introduction text for the bulletin.
    /// </summary>
    public string? Introduction { get; set; }

    /// <summary>
    /// Optional closing notes for the bulletin.
    /// </summary>
    public string? ClosingNotes { get; set; }
}
