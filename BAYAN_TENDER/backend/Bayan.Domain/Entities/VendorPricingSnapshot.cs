using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a snapshot of vendor pricing for historical tracking.
/// </summary>
public class VendorPricingSnapshot : BaseEntity
{
    /// <summary>
    /// Bidder this snapshot is for.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Tender this snapshot is from.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bid submission this snapshot is based on.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Date of the snapshot.
    /// </summary>
    public DateTime SnapshotDate { get; set; }

    /// <summary>
    /// Base currency of the tender.
    /// </summary>
    public string TenderBaseCurrency { get; set; } = string.Empty;

    /// <summary>
    /// Total bid amount.
    /// </summary>
    public decimal TotalBidAmount { get; set; }

    /// <summary>
    /// Total number of items.
    /// </summary>
    public int TotalItemsCount { get; set; }

    // Navigation properties
    /// <summary>
    /// Bidder associated with this snapshot.
    /// </summary>
    public virtual Bidder Bidder { get; set; } = null!;

    /// <summary>
    /// Tender associated with this snapshot.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Bid submission associated with this snapshot.
    /// </summary>
    public virtual BidSubmission BidSubmission { get; set; } = null!;

    /// <summary>
    /// Item rates in this snapshot.
    /// </summary>
    public virtual ICollection<VendorItemRate> ItemRates { get; set; } = new List<VendorItemRate>();
}
