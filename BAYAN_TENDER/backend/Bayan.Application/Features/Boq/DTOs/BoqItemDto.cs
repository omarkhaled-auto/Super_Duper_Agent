using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// Data transfer object for BOQ item.
/// </summary>
public class BoqItemDto
{
    /// <summary>
    /// Unique identifier for the item.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Item number (e.g., "1.1.1", "1.1.2").
    /// </summary>
    public string ItemNumber { get; set; } = string.Empty;

    /// <summary>
    /// Item description.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Quantity.
    /// </summary>
    public decimal Quantity { get; set; }

    /// <summary>
    /// Unit of measurement code.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Type of item (Base, Alternate, ProvisionalSum, Daywork).
    /// </summary>
    public BoqItemType ItemType { get; set; }

    /// <summary>
    /// Additional notes.
    /// </summary>
    public string? Notes { get; set; }

    /// <summary>
    /// Section ID this item belongs to.
    /// </summary>
    public Guid SectionId { get; set; }

    /// <summary>
    /// Sort order for display.
    /// </summary>
    public int SortOrder { get; set; }
}
