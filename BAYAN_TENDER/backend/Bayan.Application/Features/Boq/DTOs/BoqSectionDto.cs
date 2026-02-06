namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// Data transfer object for BOQ section.
/// </summary>
public class BoqSectionDto
{
    /// <summary>
    /// Unique identifier for the section.
    /// </summary>
    public Guid Id { get; set; }

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

    /// <summary>
    /// Items in this section.
    /// </summary>
    public List<BoqItemDto> Items { get; set; } = new();
}
