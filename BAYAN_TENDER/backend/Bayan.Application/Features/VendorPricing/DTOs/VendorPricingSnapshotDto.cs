namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for vendor pricing snapshot summary.
/// </summary>
public class VendorPricingSnapshotDto
{
    /// <summary>
    /// Unique identifier for the snapshot.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Bidder identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderName { get; set; } = string.Empty;

    /// <summary>
    /// Tender identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender reference number.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Date when the snapshot was taken.
    /// </summary>
    public DateTime SnapshotDate { get; set; }

    /// <summary>
    /// Number of items in the snapshot.
    /// </summary>
    public int ItemCount { get; set; }

    /// <summary>
    /// Total bid amount.
    /// </summary>
    public decimal TotalBidAmount { get; set; }

    /// <summary>
    /// Base currency of the tender.
    /// </summary>
    public string Currency { get; set; } = string.Empty;
}
