using Bayan.Domain.Enums;

namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Data transfer object for bid item to BOQ item matching.
/// </summary>
public class BidItemMatchDto
{
    /// <summary>
    /// Temporary ID for the bid item during import.
    /// </summary>
    public int RowIndex { get; set; }

    // Bid item details
    /// <summary>
    /// Bidder's item number.
    /// </summary>
    public string? BidItemNumber { get; set; }

    /// <summary>
    /// Bidder's description.
    /// </summary>
    public string? BidDescription { get; set; }

    /// <summary>
    /// Bidder's quantity.
    /// </summary>
    public decimal? BidQuantity { get; set; }

    /// <summary>
    /// Bidder's unit of measurement.
    /// </summary>
    public string? BidUom { get; set; }

    /// <summary>
    /// Bidder's unit rate.
    /// </summary>
    public decimal? BidUnitRate { get; set; }

    /// <summary>
    /// Bidder's total amount.
    /// </summary>
    public decimal? BidAmount { get; set; }

    /// <summary>
    /// Currency code.
    /// </summary>
    public string? Currency { get; set; }

    // Matched BOQ item details
    /// <summary>
    /// Matched BOQ item ID.
    /// </summary>
    public Guid? MatchedBoqItemId { get; set; }

    /// <summary>
    /// Matched BOQ item number.
    /// </summary>
    public string? MatchedBoqItemNumber { get; set; }

    /// <summary>
    /// Matched BOQ item description.
    /// </summary>
    public string? MatchedBoqDescription { get; set; }

    /// <summary>
    /// Matched BOQ quantity.
    /// </summary>
    public decimal? MatchedBoqQuantity { get; set; }

    /// <summary>
    /// Matched BOQ unit of measurement.
    /// </summary>
    public string? MatchedBoqUom { get; set; }

    // Match information
    /// <summary>
    /// Type of match (Exact, Fuzzy, Manual, ExtraItem, NoBid).
    /// </summary>
    public Domain.Enums.MatchType MatchType { get; set; }

    /// <summary>
    /// Match confidence percentage (0-100).
    /// </summary>
    public decimal Confidence { get; set; }

    /// <summary>
    /// Whether this match needs manual review.
    /// </summary>
    public bool NeedsReview { get; set; }

    /// <summary>
    /// Reason for needing review (if applicable).
    /// </summary>
    public string? ReviewReason { get; set; }

    /// <summary>
    /// Alternative BOQ items that could potentially match.
    /// </summary>
    public List<PotentialMatchDto> AlternativeMatches { get; set; } = new();
}

/// <summary>
/// Represents a potential alternative match for a bid item.
/// </summary>
public class PotentialMatchDto
{
    /// <summary>
    /// BOQ item ID.
    /// </summary>
    public Guid BoqItemId { get; set; }

    /// <summary>
    /// BOQ item number.
    /// </summary>
    public string ItemNumber { get; set; } = string.Empty;

    /// <summary>
    /// BOQ item description.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// BOQ quantity.
    /// </summary>
    public decimal Quantity { get; set; }

    /// <summary>
    /// BOQ unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Match confidence percentage.
    /// </summary>
    public decimal Confidence { get; set; }
}
