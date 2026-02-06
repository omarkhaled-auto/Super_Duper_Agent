using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Evaluation.DTOs;

/// <summary>
/// Comparable sheet summary statistics.
/// </summary>
public class ComparableSheetSummaryDto
{
    /// <summary>
    /// Total number of BOQ items.
    /// </summary>
    public int TotalItems { get; set; }

    /// <summary>
    /// Total number of bidders.
    /// </summary>
    public int BidderCount { get; set; }

    /// <summary>
    /// Total number of outlier rates detected.
    /// </summary>
    public int OutlierCount { get; set; }

    /// <summary>
    /// Maximum deviation percentage from average.
    /// </summary>
    public decimal MaxDeviation { get; set; }
}

/// <summary>
/// Bidder summary for comparable sheet.
/// </summary>
public class ComparableSheetBidderDto
{
    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Bid submission ID.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Total normalized amount.
    /// </summary>
    public decimal TotalNormalizedAmount { get; set; }

    /// <summary>
    /// Rank based on total (lowest = 1).
    /// </summary>
    public int Rank { get; set; }
}

/// <summary>
/// Bidder rate for a specific BOQ item.
/// </summary>
public class BidderRateDto
{
    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bid submission ID.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Normalized unit rate.
    /// </summary>
    public decimal? Rate { get; set; }

    /// <summary>
    /// Normalized amount (rate * qty).
    /// </summary>
    public decimal? Amount { get; set; }

    /// <summary>
    /// Whether this rate is an outlier.
    /// </summary>
    public bool IsOutlier { get; set; }

    /// <summary>
    /// Outlier severity level.
    /// </summary>
    public OutlierSeverity? Severity { get; set; }

    /// <summary>
    /// Deviation percentage from average.
    /// </summary>
    public decimal? Deviation { get; set; }

    /// <summary>
    /// Whether the bidder did not bid on this item.
    /// </summary>
    public bool IsNoBid { get; set; }

    /// <summary>
    /// Whether the item is non-comparable for this bidder.
    /// </summary>
    public bool IsNonComparable { get; set; }
}

/// <summary>
/// BOQ item row in comparable sheet.
/// </summary>
public class ComparableSheetItemDto
{
    /// <summary>
    /// BOQ item ID.
    /// </summary>
    public Guid BoqItemId { get; set; }

    /// <summary>
    /// Item number.
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
    /// Section ID.
    /// </summary>
    public Guid SectionId { get; set; }

    /// <summary>
    /// Section name.
    /// </summary>
    public string SectionName { get; set; } = string.Empty;

    /// <summary>
    /// Item type.
    /// </summary>
    public BoqItemType ItemType { get; set; }

    /// <summary>
    /// Sort order.
    /// </summary>
    public int SortOrder { get; set; }

    /// <summary>
    /// Average rate across all bidders (excluding NoBid and NonComparable).
    /// </summary>
    public decimal? AverageRate { get; set; }

    /// <summary>
    /// Bidder rates for this item.
    /// </summary>
    public List<BidderRateDto> BidderRates { get; set; } = new();
}

/// <summary>
/// Bidder total for a section.
/// </summary>
public class BidderSectionTotalDto
{
    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Total amount for this section.
    /// </summary>
    public decimal Total { get; set; }
}

/// <summary>
/// Section total row in comparable sheet.
/// </summary>
public class ComparableSheetSectionTotalDto
{
    /// <summary>
    /// Section ID.
    /// </summary>
    public Guid SectionId { get; set; }

    /// <summary>
    /// Section name.
    /// </summary>
    public string SectionName { get; set; } = string.Empty;

    /// <summary>
    /// Sort order.
    /// </summary>
    public int SortOrder { get; set; }

    /// <summary>
    /// Bidder totals for this section.
    /// </summary>
    public List<BidderSectionTotalDto> BidderTotals { get; set; } = new();
}

/// <summary>
/// Grand total for a bidder.
/// </summary>
public class BidderGrandTotalDto
{
    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Grand total amount.
    /// </summary>
    public decimal GrandTotal { get; set; }
}

/// <summary>
/// Complete comparable sheet DTO.
/// </summary>
public class ComparableSheetDto
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender name/title.
    /// </summary>
    public string TenderName { get; set; } = string.Empty;

    /// <summary>
    /// Summary statistics.
    /// </summary>
    public ComparableSheetSummaryDto Summary { get; set; } = new();

    /// <summary>
    /// List of bidders with their totals and ranks.
    /// </summary>
    public List<ComparableSheetBidderDto> Bidders { get; set; } = new();

    /// <summary>
    /// List of BOQ items with bidder rates.
    /// </summary>
    public List<ComparableSheetItemDto> Items { get; set; } = new();

    /// <summary>
    /// Section totals.
    /// </summary>
    public List<ComparableSheetSectionTotalDto> SectionTotals { get; set; } = new();

    /// <summary>
    /// Grand totals per bidder.
    /// </summary>
    public List<BidderGrandTotalDto> GrandTotals { get; set; } = new();

    /// <summary>
    /// When the comparable sheet was generated.
    /// </summary>
    public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

    /// <summary>
    /// Warning message when fewer than 3 bidders are present.
    /// </summary>
    public string? MinimumBiddersWarning { get; set; }
}

/// <summary>
/// Options for filtering the comparable sheet.
/// </summary>
public class ComparableSheetOptionsDto
{
    /// <summary>
    /// Whether to include provisional sums.
    /// </summary>
    public bool IncludeProvisionalSums { get; set; } = true;

    /// <summary>
    /// Whether to include alternates.
    /// </summary>
    public bool IncludeAlternates { get; set; } = true;

    /// <summary>
    /// Whether to include daywork items.
    /// </summary>
    public bool IncludeDaywork { get; set; } = true;
}

/// <summary>
/// Result of outlier recalculation.
/// </summary>
public class OutlierRecalculationResultDto
{
    /// <summary>
    /// Number of items processed.
    /// </summary>
    public int ItemsProcessed { get; set; }

    /// <summary>
    /// Number of outliers detected.
    /// </summary>
    public int OutliersDetected { get; set; }

    /// <summary>
    /// High severity outliers.
    /// </summary>
    public int HighSeverityCount { get; set; }

    /// <summary>
    /// Medium severity outliers.
    /// </summary>
    public int MediumSeverityCount { get; set; }

    /// <summary>
    /// Low severity outliers (within threshold).
    /// </summary>
    public int LowSeverityCount { get; set; }

    /// <summary>
    /// When the recalculation was performed.
    /// </summary>
    public DateTime CalculatedAt { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Result of commercial score calculation.
/// </summary>
public class CommercialScoreResultDto
{
    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Normalized total price.
    /// </summary>
    public decimal NormalizedTotalPrice { get; set; }

    /// <summary>
    /// Commercial score (Lowest/This * 100).
    /// </summary>
    public decimal CommercialScore { get; set; }

    /// <summary>
    /// Rank based on commercial score (highest = 1).
    /// </summary>
    public int Rank { get; set; }
}

/// <summary>
/// Result of commercial scores calculation.
/// </summary>
public class CalculateCommercialScoresResultDto
{
    /// <summary>
    /// List of bidder scores.
    /// </summary>
    public List<CommercialScoreResultDto> Scores { get; set; } = new();

    /// <summary>
    /// Lowest bid amount.
    /// </summary>
    public decimal LowestBidAmount { get; set; }

    /// <summary>
    /// Whether provisional sums were included.
    /// </summary>
    public bool IncludeProvisionalSums { get; set; }

    /// <summary>
    /// Whether alternates were included.
    /// </summary>
    public bool IncludeAlternates { get; set; }

    /// <summary>
    /// When the scores were calculated.
    /// </summary>
    public DateTime CalculatedAt { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Result of comparable sheet export.
/// </summary>
public class ExportComparableSheetResultDto
{
    /// <summary>
    /// File content as byte array.
    /// </summary>
    public byte[] FileContent { get; set; } = Array.Empty<byte>();

    /// <summary>
    /// File name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Content type.
    /// </summary>
    public string ContentType { get; set; } = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
}
