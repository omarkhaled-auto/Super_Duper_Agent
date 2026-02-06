namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for a vendor's item rate.
/// </summary>
public class VendorItemRateDto
{
    /// <summary>
    /// Unique identifier for the rate record.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Item description.
    /// </summary>
    public string ItemDescription { get; set; } = string.Empty;

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Normalized unit rate.
    /// </summary>
    public decimal Rate { get; set; }

    /// <summary>
    /// Currency of the rate.
    /// </summary>
    public string Currency { get; set; } = string.Empty;

    /// <summary>
    /// Quantity quoted.
    /// </summary>
    public decimal? Quantity { get; set; }

    /// <summary>
    /// Total amount (rate * quantity).
    /// </summary>
    public decimal? TotalAmount { get; set; }

    /// <summary>
    /// Tender reference number this rate came from.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Date when this rate was captured.
    /// </summary>
    public DateTime SnapshotDate { get; set; }

    /// <summary>
    /// BOQ item identifier (if linked).
    /// </summary>
    public Guid? BoqItemId { get; set; }
}
