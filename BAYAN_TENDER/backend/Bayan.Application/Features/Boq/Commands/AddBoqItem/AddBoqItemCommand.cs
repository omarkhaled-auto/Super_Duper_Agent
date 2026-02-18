using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Boq.Commands.AddBoqItem;

/// <summary>
/// Command for adding a new BOQ item.
/// </summary>
public class AddBoqItemCommand : IRequest<BoqItemDto>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Section ID this item belongs to.
    /// </summary>
    public Guid SectionId { get; set; }

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
    public BoqItemType ItemType { get; set; } = BoqItemType.Base;

    /// <summary>
    /// Additional notes.
    /// </summary>
    public string? Notes { get; set; }

    /// <summary>
    /// Sort order for display.
    /// </summary>
    public int SortOrder { get; set; }

    /// <summary>
    /// Parent item ID for sub-items in a hierarchical BOQ.
    /// Null for top-level items.
    /// </summary>
    public Guid? ParentItemId { get; set; }

    /// <summary>
    /// Whether this item is a group header that contains child sub-items.
    /// </summary>
    public bool IsGroup { get; set; } = false;
}
