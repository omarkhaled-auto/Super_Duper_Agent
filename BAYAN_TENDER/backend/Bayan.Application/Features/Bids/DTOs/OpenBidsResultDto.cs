namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Result of opening all bids for a tender.
/// This is an IRREVERSIBLE action.
/// </summary>
public class OpenBidsResultDto
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Reference number of the tender.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Number of bids that were opened.
    /// </summary>
    public int BidsOpenedCount { get; set; }

    /// <summary>
    /// Timestamp when bids were opened.
    /// </summary>
    public DateTime OpenedAt { get; set; }

    /// <summary>
    /// User who opened the bids.
    /// </summary>
    public Guid OpenedBy { get; set; }

    /// <summary>
    /// Name of user who opened the bids.
    /// </summary>
    public string OpenedByName { get; set; } = string.Empty;

    /// <summary>
    /// List of opened bid summaries.
    /// </summary>
    public List<OpenedBidSummaryDto> OpenedBids { get; set; } = new();

    /// <summary>
    /// Audit log entry ID for this action.
    /// </summary>
    public Guid AuditLogId { get; set; }
}

/// <summary>
/// Summary of an opened bid.
/// </summary>
public class OpenedBidSummaryDto
{
    /// <summary>
    /// Bid submission ID.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderName { get; set; } = string.Empty;

    /// <summary>
    /// Currency of the bid.
    /// </summary>
    public string NativeCurrency { get; set; } = string.Empty;

    /// <summary>
    /// Total amount in native currency.
    /// </summary>
    public decimal? NativeTotalAmount { get; set; }

    /// <summary>
    /// Total amount in tender base currency.
    /// </summary>
    public decimal? NormalizedTotalAmount { get; set; }

    /// <summary>
    /// Whether the bid was late.
    /// </summary>
    public bool IsLate { get; set; }

    /// <summary>
    /// Whether the late bid was accepted.
    /// </summary>
    public bool? LateAccepted { get; set; }
}
