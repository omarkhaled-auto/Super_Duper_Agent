namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Represents a unit of measure mismatch between bidder and master BOQ.
/// </summary>
public class UomMismatchDto
{
    /// <summary>
    /// BOQ item identifier.
    /// </summary>
    public Guid ItemId { get; set; }

    /// <summary>
    /// BOQ item number (e.g., "1.1.1").
    /// </summary>
    public string ItemNumber { get; set; } = string.Empty;

    /// <summary>
    /// Item description for reference.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Unit of measure provided by the bidder.
    /// </summary>
    public string BidderUom { get; set; } = string.Empty;

    /// <summary>
    /// Unit of measure in the master BOQ.
    /// </summary>
    public string MasterUom { get; set; } = string.Empty;

    /// <summary>
    /// Conversion factor from bidder UOM to master UOM.
    /// Null if conversion is not possible.
    /// </summary>
    public decimal? ConversionFactor { get; set; }

    /// <summary>
    /// Whether automatic conversion is possible between the two UOMs.
    /// </summary>
    public bool CanConvert { get; set; }

    /// <summary>
    /// Reason for non-convertibility (e.g., "Different categories: Lump vs Area").
    /// </summary>
    public string? NonConvertibleReason { get; set; }
}
