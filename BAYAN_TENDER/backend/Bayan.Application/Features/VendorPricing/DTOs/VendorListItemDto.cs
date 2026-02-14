namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for a vendor in the vendor list.
/// </summary>
public class VendorListItemDto
{
    /// <summary>
    /// Bidder identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Contact person.
    /// </summary>
    public string ContactPerson { get; set; } = string.Empty;

    /// <summary>
    /// Contact email.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Trade specialization.
    /// </summary>
    public string? TradeSpecialization { get; set; }

    /// <summary>
    /// Total number of pricing snapshots.
    /// </summary>
    public int SnapshotCount { get; set; }

    /// <summary>
    /// Total number of tenders with pricing data.
    /// </summary>
    public int TenderCount { get; set; }

    /// <summary>
    /// Date of the most recent pricing snapshot.
    /// </summary>
    public DateTime? LastPricingDate { get; set; }

    /// <summary>
    /// Total bid value across all pricing snapshots.
    /// </summary>
    public decimal TotalBidValue { get; set; }

    /// <summary>
    /// Whether the bidder is currently active.
    /// </summary>
    public bool IsActive { get; set; }
}
