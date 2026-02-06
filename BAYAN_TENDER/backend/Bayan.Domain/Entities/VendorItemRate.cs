using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a single item rate in a vendor pricing snapshot.
/// </summary>
public class VendorItemRate : BaseEntity
{
    /// <summary>
    /// Snapshot this rate belongs to.
    /// </summary>
    public Guid SnapshotId { get; set; }

    /// <summary>
    /// BOQ item reference (may be null for cross-tender items).
    /// </summary>
    public Guid? BoqItemId { get; set; }

    /// <summary>
    /// Item description (denormalized for cross-tender comparison).
    /// </summary>
    public string ItemDescription { get; set; } = string.Empty;

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Normalized unit rate.
    /// </summary>
    public decimal NormalizedUnitRate { get; set; }

    /// <summary>
    /// Normalized currency.
    /// </summary>
    public string NormalizedCurrency { get; set; } = string.Empty;

    /// <summary>
    /// Quantity.
    /// </summary>
    public decimal? Quantity { get; set; }

    /// <summary>
    /// Total amount.
    /// </summary>
    public decimal? TotalAmount { get; set; }

    // Navigation properties
    /// <summary>
    /// Snapshot associated with this rate.
    /// </summary>
    public virtual VendorPricingSnapshot Snapshot { get; set; } = null!;

    /// <summary>
    /// BOQ item reference.
    /// </summary>
    public virtual BoqItem? BoqItem { get; set; }
}
