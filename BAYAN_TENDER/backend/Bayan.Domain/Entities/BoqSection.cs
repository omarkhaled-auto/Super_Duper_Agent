using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a section in the Bill of Quantities.
/// </summary>
public class BoqSection : BaseEntity
{
    /// <summary>
    /// Tender this section belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Parent section (null for top-level sections).
    /// </summary>
    public Guid? ParentSectionId { get; set; }

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

    // Navigation properties
    /// <summary>
    /// Tender associated with this section.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Parent section.
    /// </summary>
    public virtual BoqSection? ParentSection { get; set; }

    /// <summary>
    /// Child sections.
    /// </summary>
    public virtual ICollection<BoqSection> ChildSections { get; set; } = new List<BoqSection>();

    /// <summary>
    /// Items in this section.
    /// </summary>
    public virtual ICollection<BoqItem> Items { get; set; } = new List<BoqItem>();
}
