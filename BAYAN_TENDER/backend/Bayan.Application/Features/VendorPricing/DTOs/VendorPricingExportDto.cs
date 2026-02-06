namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for vendor pricing export result.
/// </summary>
public class VendorPricingExportDto
{
    /// <summary>
    /// File name for the export.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Content type for the file.
    /// </summary>
    public string ContentType { get; set; } = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

    /// <summary>
    /// File content as byte array.
    /// </summary>
    public byte[] Content { get; set; } = Array.Empty<byte>();

    /// <summary>
    /// Number of records exported.
    /// </summary>
    public int RecordCount { get; set; }

    /// <summary>
    /// Export date/time.
    /// </summary>
    public DateTime ExportedAt { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Row data for vendor pricing export.
/// </summary>
public class VendorPricingExportRowDto
{
    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string VendorName { get; set; } = string.Empty;

    /// <summary>
    /// Trade specialization.
    /// </summary>
    public string? Trade { get; set; }

    /// <summary>
    /// Tender reference.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Date of the bid/snapshot.
    /// </summary>
    public DateTime Date { get; set; }

    /// <summary>
    /// Item description.
    /// </summary>
    public string ItemDescription { get; set; } = string.Empty;

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Unit rate.
    /// </summary>
    public decimal Rate { get; set; }

    /// <summary>
    /// Quantity.
    /// </summary>
    public decimal? Quantity { get; set; }

    /// <summary>
    /// Total amount.
    /// </summary>
    public decimal? TotalAmount { get; set; }

    /// <summary>
    /// Currency.
    /// </summary>
    public string Currency { get; set; } = string.Empty;
}
