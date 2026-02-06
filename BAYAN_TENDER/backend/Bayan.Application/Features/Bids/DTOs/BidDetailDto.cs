using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Data transfer object for full bid details including all files.
/// </summary>
public class BidDetailDto
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
    /// Reference number of the tender.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Title of the tender.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

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
    /// Bidder's phone number.
    /// </summary>
    public string? BidderPhone { get; set; }

    /// <summary>
    /// Commercial Registration Number.
    /// </summary>
    public string? CRNumber { get; set; }

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
    /// User who accepted the late submission.
    /// </summary>
    public Guid? LateAcceptedBy { get; set; }

    /// <summary>
    /// Name of user who accepted the late submission.
    /// </summary>
    public string? LateAcceptedByName { get; set; }

    /// <summary>
    /// Receipt number for the submission.
    /// </summary>
    public string ReceiptNumber { get; set; } = string.Empty;

    /// <summary>
    /// Path to receipt PDF in storage.
    /// </summary>
    public string? ReceiptPdfPath { get; set; }

    /// <summary>
    /// Original uploaded file name.
    /// </summary>
    public string? OriginalFileName { get; set; }

    /// <summary>
    /// Currency of the bid.
    /// </summary>
    public string NativeCurrency { get; set; } = "AED";

    /// <summary>
    /// Total bid amount in native currency.
    /// Only visible when Status = Opened.
    /// </summary>
    public decimal? NativeTotalAmount { get; set; }

    /// <summary>
    /// Exchange rate applied.
    /// </summary>
    public decimal FxRate { get; set; } = 1.0m;

    /// <summary>
    /// Total amount normalized to tender base currency.
    /// Only visible when Status = Opened.
    /// </summary>
    public decimal? NormalizedTotalAmount { get; set; }

    /// <summary>
    /// Bid validity period in days.
    /// </summary>
    public int BidValidityDays { get; set; }

    /// <summary>
    /// Import status of the bid.
    /// </summary>
    public BidImportStatus ImportStatus { get; set; }

    /// <summary>
    /// When import started.
    /// </summary>
    public DateTime? ImportStartedAt { get; set; }

    /// <summary>
    /// When import completed.
    /// </summary>
    public DateTime? ImportCompletedAt { get; set; }

    /// <summary>
    /// User who performed the import.
    /// </summary>
    public Guid? ImportedBy { get; set; }

    /// <summary>
    /// Name of user who performed the import.
    /// </summary>
    public string? ImportedByName { get; set; }

    /// <summary>
    /// Validation summary (JSON).
    /// </summary>
    public string? ValidationSummary { get; set; }

    /// <summary>
    /// Reason for disqualification (if applicable).
    /// </summary>
    public string? DisqualificationReason { get; set; }

    /// <summary>
    /// Reason for late bid rejection (if applicable).
    /// </summary>
    public string? LateBidRejectionReason { get; set; }

    /// <summary>
    /// Documents included in this submission.
    /// </summary>
    public List<BidDocumentDto> Documents { get; set; } = new();

    /// <summary>
    /// When the bid was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }
}

/// <summary>
/// Data transfer object for bid document details.
/// </summary>
public class BidDocumentDto
{
    /// <summary>
    /// Unique identifier for the document.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Type of document.
    /// </summary>
    public BidDocumentType DocumentType { get; set; }

    /// <summary>
    /// Document type display name.
    /// </summary>
    public string DocumentTypeName { get; set; } = string.Empty;

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSizeBytes { get; set; }

    /// <summary>
    /// MIME content type.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// When the document was uploaded.
    /// </summary>
    public DateTime UploadedAt { get; set; }

    /// <summary>
    /// Category: Commercial or Technical.
    /// </summary>
    public string Category { get; set; } = string.Empty;
}
