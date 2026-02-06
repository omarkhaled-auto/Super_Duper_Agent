using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a bid submission from a bidder.
/// </summary>
public class BidSubmission : BaseEntity
{
    /// <summary>
    /// Tender this submission is for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder who submitted.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// When the bid was submitted.
    /// </summary>
    public DateTime SubmissionTime { get; set; }

    /// <summary>
    /// Whether the submission was late.
    /// </summary>
    public bool IsLate { get; set; }

    /// <summary>
    /// Whether the late submission was accepted.
    /// </summary>
    public bool? LateAccepted { get; set; }

    /// <summary>
    /// User who accepted the late submission.
    /// </summary>
    public Guid? LateAcceptedBy { get; set; }

    /// <summary>
    /// Original uploaded file name.
    /// </summary>
    public string? OriginalFileName { get; set; }

    /// <summary>
    /// Path to original file in MinIO.
    /// </summary>
    public string? OriginalFilePath { get; set; }

    /// <summary>
    /// Currency of the bid.
    /// </summary>
    public string NativeCurrency { get; set; } = "AED";

    /// <summary>
    /// Total bid amount in native currency.
    /// </summary>
    public decimal? NativeTotalAmount { get; set; }

    /// <summary>
    /// Exchange rate applied.
    /// </summary>
    public decimal FxRate { get; set; } = 1.0m;

    /// <summary>
    /// Total amount in tender base currency.
    /// </summary>
    public decimal? NormalizedTotalAmount { get; set; }

    /// <summary>
    /// Bid validity period in days.
    /// </summary>
    public int BidValidityDays { get; set; } = 90;

    /// <summary>
    /// Import status.
    /// </summary>
    public BidImportStatus ImportStatus { get; set; } = BidImportStatus.Uploaded;

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
    /// Validation summary as JSON.
    /// </summary>
    public string? ValidationSummary { get; set; }

    /// <summary>
    /// Receipt number.
    /// </summary>
    public string ReceiptNumber { get; set; } = string.Empty;

    /// <summary>
    /// Path to receipt PDF in MinIO.
    /// </summary>
    public string? ReceiptPdfPath { get; set; }

    /// <summary>
    /// Submission status.
    /// </summary>
    public BidSubmissionStatus Status { get; set; } = BidSubmissionStatus.Submitted;

    // Navigation properties
    /// <summary>
    /// Tender associated with this submission.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Bidder who submitted.
    /// </summary>
    public virtual Bidder Bidder { get; set; } = null!;

    /// <summary>
    /// User who accepted the late submission.
    /// </summary>
    public virtual User? LateAcceptedByUser { get; set; }

    /// <summary>
    /// User who imported the bid.
    /// </summary>
    public virtual User? Importer { get; set; }

    /// <summary>
    /// Documents included in this submission.
    /// </summary>
    public virtual ICollection<BidDocument> BidDocuments { get; set; } = new List<BidDocument>();

    /// <summary>
    /// Pricing line items.
    /// </summary>
    public virtual ICollection<BidPricing> BidPricings { get; set; } = new List<BidPricing>();

    /// <summary>
    /// Vendor pricing snapshot for this submission.
    /// </summary>
    public virtual VendorPricingSnapshot? VendorPricingSnapshot { get; set; }
}
