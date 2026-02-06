using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Data transfer object for bid list view.
/// Amounts are hidden until bids are opened.
/// </summary>
public class BidListDto
{
    /// <summary>
    /// Unique identifier for the bid submission.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// ID of the tender this bid belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the bidder who submitted.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Name of the bidding company.
    /// </summary>
    public string BidderName { get; set; } = string.Empty;

    /// <summary>
    /// Contact person at the bidding company.
    /// </summary>
    public string ContactPerson { get; set; } = string.Empty;

    /// <summary>
    /// Bidder's email address.
    /// </summary>
    public string BidderEmail { get; set; } = string.Empty;

    /// <summary>
    /// When the bid was submitted.
    /// </summary>
    public DateTime SubmissionTime { get; set; }

    /// <summary>
    /// Current status of the bid.
    /// </summary>
    public BidSubmissionStatus Status { get; set; }

    /// <summary>
    /// Whether this bid was submitted late.
    /// </summary>
    public bool IsLate { get; set; }

    /// <summary>
    /// If late, whether it was accepted (null = pending decision).
    /// </summary>
    public bool? LateAccepted { get; set; }

    /// <summary>
    /// Receipt number for the submission.
    /// </summary>
    public string ReceiptNumber { get; set; } = string.Empty;

    /// <summary>
    /// Currency of the bid.
    /// Only visible when Status = Opened.
    /// </summary>
    public string? NativeCurrency { get; set; }

    /// <summary>
    /// Total bid amount in native currency.
    /// Only visible when Status = Opened.
    /// </summary>
    public decimal? NativeTotalAmount { get; set; }

    /// <summary>
    /// Total amount normalized to tender base currency.
    /// Only visible when Status = Opened.
    /// </summary>
    public decimal? NormalizedTotalAmount { get; set; }

    /// <summary>
    /// Number of commercial/pricing documents attached.
    /// </summary>
    public int CommercialFileCount { get; set; }

    /// <summary>
    /// Number of technical documents attached.
    /// </summary>
    public int TechnicalFileCount { get; set; }

    /// <summary>
    /// Total number of files attached.
    /// </summary>
    public int TotalFileCount { get; set; }

    /// <summary>
    /// Import status of the bid.
    /// </summary>
    public BidImportStatus ImportStatus { get; set; }
}
