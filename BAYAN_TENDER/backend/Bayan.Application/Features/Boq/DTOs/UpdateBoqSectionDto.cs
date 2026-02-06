namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// Data transfer object for updating an existing BOQ section.
/// </summary>
public class UpdateBoqSectionDto
{
    /// <summary>
    /// Section number (e.g., "1", "1.1", "2").
    /// </summary>
    public string SectionNumber { get; set; } = string.Empty;

    /// <summary>
    /// Section title.
    /// </summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Sort order for display.
    /// </summary>
    public int SortOrder { get; set; }

    /// <summary>
    /// Parent section ID (null for top-level sections).
    /// </summary>
    public Guid? ParentSectionId { get; set; }
}
