namespace Bayan.Application.Features.Documents.DTOs;

/// <summary>
/// Data transfer object for Document entity.
/// </summary>
public class DocumentDto
{
    /// <summary>
    /// Unique identifier for the document.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Tender this document belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Original file name.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Folder path within the tender (e.g., "RFP Package", "Drawings").
    /// </summary>
    public string Folder { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long Size { get; set; }

    /// <summary>
    /// Human-readable file size.
    /// </summary>
    public string SizeFormatted { get; set; } = string.Empty;

    /// <summary>
    /// MIME content type.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// Document version number.
    /// </summary>
    public int Version { get; set; }

    /// <summary>
    /// Whether this is the latest version.
    /// </summary>
    public bool IsLatest { get; set; }

    /// <summary>
    /// Timestamp when the document was uploaded.
    /// </summary>
    public DateTime UploadedAt { get; set; }

    /// <summary>
    /// ID of the user who uploaded the document.
    /// </summary>
    public Guid UploadedBy { get; set; }

    /// <summary>
    /// Name of the user who uploaded the document.
    /// </summary>
    public string UploadedByName { get; set; } = string.Empty;
}
