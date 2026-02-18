using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents an item in the Bill of Quantities.
/// </summary>
public class BoqItem : BaseEntity
{
    /// <summary>
    /// Tender this item belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Section this item belongs to.
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
    /// Unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Type of item.
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
    /// Null for top-level items and standalone items.
    /// </summary>
    public Guid? ParentItemId { get; set; }

    /// <summary>
    /// Whether this item is a group header that contains child sub-items.
    /// Group items typically have no quantity/UOM of their own.
    /// </summary>
    public bool IsGroup { get; set; } = false;

    // Navigation properties
    /// <summary>
    /// Tender associated with this item.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Section this item belongs to.
    /// </summary>
    public virtual BoqSection Section { get; set; } = null!;

    /// <summary>
    /// Parent item (for sub-items in hierarchical BOQ).
    /// </summary>
    public virtual BoqItem? ParentItem { get; set; }

    /// <summary>
    /// Child sub-items (for group items in hierarchical BOQ).
    /// </summary>
    public virtual ICollection<BoqItem> ChildItems { get; set; } = new List<BoqItem>();

    /// <summary>
    /// Bid pricing entries for this item.
    /// </summary>
    public virtual ICollection<BidPricing> BidPricings { get; set; } = new List<BidPricing>();

    /// <summary>
    /// Vendor item rates for this item.
    /// </summary>
    public virtual ICollection<VendorItemRate> VendorItemRates { get; set; } = new List<VendorItemRate>();
}
