namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Result of bid normalization containing FX rate, UOM mismatches, and normalized items.
/// </summary>
public class NormalizationResultDto
{
    /// <summary>
    /// Bid submission identifier.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Tender identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderCompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Native currency of the bid.
    /// </summary>
    public string NativeCurrency { get; set; } = string.Empty;

    /// <summary>
    /// Base currency of the tender.
    /// </summary>
    public string BaseCurrency { get; set; } = "AED";

    /// <summary>
    /// Exchange rate applied (native to base).
    /// </summary>
    public decimal FxRate { get; set; } = 1.0m;

    /// <summary>
    /// FX rate source (e.g., "Manual", "API", "System Default").
    /// </summary>
    public string FxRateSource { get; set; } = "System Default";

    /// <summary>
    /// Date when FX rate was captured.
    /// </summary>
    public DateTime? FxRateDate { get; set; }

    /// <summary>
    /// Original total amount in native currency.
    /// </summary>
    public decimal? OriginalTotalAmount { get; set; }

    /// <summary>
    /// Normalized total amount in base currency.
    /// </summary>
    public decimal? NormalizedTotalAmount { get; set; }

    /// <summary>
    /// Total number of line items processed.
    /// </summary>
    public int TotalItemsCount { get; set; }

    /// <summary>
    /// Number of items successfully normalized.
    /// </summary>
    public int NormalizedItemsCount { get; set; }

    /// <summary>
    /// Number of items with UOM mismatches that could be converted.
    /// </summary>
    public int ConvertibleMismatchCount { get; set; }

    /// <summary>
    /// Number of non-comparable items (UOM cannot be converted).
    /// </summary>
    public int NonComparableCount { get; set; }

    /// <summary>
    /// List of UOM mismatches detected.
    /// </summary>
    public List<UomMismatchDto> UomMismatches { get; set; } = new();

    /// <summary>
    /// List of normalized items.
    /// </summary>
    public List<NormalizedItemDto> NormalizedItems { get; set; } = new();

    /// <summary>
    /// Whether normalization was successful.
    /// </summary>
    public bool IsSuccess { get; set; }

    /// <summary>
    /// Warnings generated during normalization.
    /// </summary>
    public List<string> Warnings { get; set; } = new();
}
