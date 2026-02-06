using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a document associated with a tender.
/// </summary>
public class Document : BaseEntity
{
    /// <summary>
    /// Tender this document belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Folder path within the tender (e.g., "RFP Package", "Drawings").
    /// </summary>
    public string FolderPath { get; set; } = string.Empty;

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
    /// Document version number.
    /// </summary>
    public int Version { get; set; } = 1;

    /// <summary>
    /// Whether this is the latest version.
    /// </summary>
    public bool IsLatest { get; set; } = true;

    /// <summary>
    /// User who uploaded the document.
    /// </summary>
    public Guid UploadedBy { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this document.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// User who uploaded the document.
    /// </summary>
    public virtual User Uploader { get; set; } = null!;

    /// <summary>
    /// Clarifications referencing this document.
    /// </summary>
    public virtual ICollection<Clarification> ReferencingClarifications { get; set; } = new List<Clarification>();
}
