using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a file attachment associated with a clarification/RFI.
/// </summary>
public class ClarificationAttachment : BaseEntity
{
    /// <summary>
    /// The clarification this attachment belongs to.
    /// </summary>
    public Guid ClarificationId { get; set; }

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Path to file in MinIO storage.
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
    /// User who uploaded the attachment (null if uploaded by bidder via portal).
    /// </summary>
    public Guid? UploadedByUserId { get; set; }

    // Navigation properties

    /// <summary>
    /// Clarification this attachment belongs to.
    /// </summary>
    public virtual Clarification Clarification { get; set; } = null!;

    /// <summary>
    /// User who uploaded the attachment.
    /// </summary>
    public virtual User? UploadedByUser { get; set; }
}
