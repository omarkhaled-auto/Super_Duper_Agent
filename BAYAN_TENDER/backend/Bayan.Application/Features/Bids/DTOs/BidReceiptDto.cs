namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Data transfer object for a bid receipt.
/// </summary>
public class BidReceiptDto
{
    /// <summary>
    /// Unique receipt number.
    /// </summary>
    public string ReceiptNumber { get; set; } = string.Empty;

    /// <summary>
    /// ID of the bid submission.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Title of the tender.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Reference number of the tender.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// When the bid was submitted.
    /// </summary>
    public DateTime SubmittedAt { get; set; }

    /// <summary>
    /// Timezone of the submission timestamp.
    /// </summary>
    public string Timezone { get; set; } = "UTC";

    /// <summary>
    /// Company name of the bidder.
    /// </summary>
    public string BidderCompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Whether the submission was late.
    /// </summary>
    public bool IsLate { get; set; }

    /// <summary>
    /// Files included in the submission.
    /// </summary>
    public List<BidReceiptFileDto> Files { get; set; } = new();
}

/// <summary>
/// Data transfer object for a file listed in the bid receipt.
/// </summary>
public class BidReceiptFileDto
{
    /// <summary>
    /// Type of document.
    /// </summary>
    public string DocumentType { get; set; } = string.Empty;

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// File size formatted for display.
    /// </summary>
    public string FileSizeFormatted { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSizeBytes { get; set; }
}
