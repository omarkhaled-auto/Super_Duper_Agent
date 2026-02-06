using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Data transfer object for a bid submission.
/// </summary>
public class BidSubmissionDto
{
    /// <summary>
    /// Unique identifier for the bid submission.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// ID of the tender this bid is for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the bidder who submitted.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Company name of the bidder.
    /// </summary>
    public string BidderCompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Contact person name of the bidder.
    /// </summary>
    public string BidderContactPerson { get; set; } = string.Empty;

    /// <summary>
    /// Email of the bidder.
    /// </summary>
    public string BidderEmail { get; set; } = string.Empty;

    /// <summary>
    /// When the bid was submitted.
    /// </summary>
    public DateTime SubmittedAt { get; set; }

    /// <summary>
    /// Whether the submission was late.
    /// </summary>
    public bool IsLate { get; set; }

    /// <summary>
    /// Whether the late submission was accepted.
    /// </summary>
    public bool? LateAccepted { get; set; }

    /// <summary>
    /// Current status of the bid submission.
    /// </summary>
    public BidSubmissionStatus Status { get; set; }

    /// <summary>
    /// Display name for the status.
    /// </summary>
    public string StatusName => Status.ToString();

    /// <summary>
    /// Receipt number for the submission.
    /// </summary>
    public string ReceiptNumber { get; set; } = string.Empty;

    /// <summary>
    /// Total bid amount in native currency.
    /// </summary>
    public decimal? TotalAmount { get; set; }

    /// <summary>
    /// Currency of the bid.
    /// </summary>
    public string Currency { get; set; } = "AED";

    /// <summary>
    /// Bid validity period in days.
    /// </summary>
    public int BidValidityDays { get; set; }

    /// <summary>
    /// Documents included in this submission.
    /// </summary>
    public List<BidDocumentDto> Documents { get; set; } = new();
}
