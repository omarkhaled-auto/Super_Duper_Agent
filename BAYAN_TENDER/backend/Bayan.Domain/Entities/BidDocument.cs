using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a document included in a bid submission.
/// </summary>
public class BidDocument : BaseEntity
{
    /// <summary>
    /// Bid submission this document belongs to.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Type of document.
    /// </summary>
    public BidDocumentType DocumentType { get; set; }

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Path to file in MinIO.
    /// </summary>
    public string FilePath { get; set; } = string.Empty;

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

    // Navigation properties
    /// <summary>
    /// Bid submission associated with this document.
    /// </summary>
    public virtual BidSubmission BidSubmission { get; set; } = null!;
}
