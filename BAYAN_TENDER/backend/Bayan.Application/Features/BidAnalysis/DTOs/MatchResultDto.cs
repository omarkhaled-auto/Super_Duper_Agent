namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Result of matching bid items to BOQ items.
/// </summary>
public class MatchResultDto
{
    /// <summary>
    /// Items matched exactly by item number.
    /// </summary>
    public List<BidItemMatchDto> ExactMatches { get; set; } = new();

    /// <summary>
    /// Items matched by fuzzy description matching.
    /// </summary>
    public List<BidItemMatchDto> FuzzyMatches { get; set; } = new();

    /// <summary>
    /// Items that could not be matched automatically.
    /// </summary>
    public List<BidItemMatchDto> Unmatched { get; set; } = new();

    /// <summary>
    /// Extra items in bid that are not in BOQ.
    /// </summary>
    public List<BidItemMatchDto> ExtraItems { get; set; } = new();

    /// <summary>
    /// BOQ items with no corresponding bid items.
    /// </summary>
    public List<NoBidItemDto> NoBidItems { get; set; } = new();

    /// <summary>
    /// Summary statistics of the matching process.
    /// </summary>
    public MatchSummaryDto Summary { get; set; } = new();
}

/// <summary>
/// BOQ item that has no corresponding bid item.
/// </summary>
public class NoBidItemDto
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
    /// Section name the item belongs to.
    /// </summary>
    public string? SectionName { get; set; }
}

/// <summary>
/// Summary statistics for the matching process.
/// </summary>
public class MatchSummaryDto
{
    /// <summary>
    /// Total number of bid items processed.
    /// </summary>
    public int TotalBidItems { get; set; }

    /// <summary>
    /// Total number of BOQ items.
    /// </summary>
    public int TotalBoqItems { get; set; }

    /// <summary>
    /// Number of exact matches.
    /// </summary>
    public int ExactMatchCount { get; set; }

    /// <summary>
    /// Number of fuzzy matches.
    /// </summary>
    public int FuzzyMatchCount { get; set; }

    /// <summary>
    /// Number of unmatched items.
    /// </summary>
    public int UnmatchedCount { get; set; }

    /// <summary>
    /// Number of extra items.
    /// </summary>
    public int ExtraItemCount { get; set; }

    /// <summary>
    /// Number of BOQ items with no bid.
    /// </summary>
    public int NoBidCount { get; set; }

    /// <summary>
    /// Overall match percentage.
    /// </summary>
    public decimal MatchPercentage { get; set; }

    /// <summary>
    /// Average confidence for fuzzy matches.
    /// </summary>
    public decimal AverageFuzzyConfidence { get; set; }

    /// <summary>
    /// Number of items requiring manual review.
    /// </summary>
    public int RequiresReviewCount { get; set; }
}
