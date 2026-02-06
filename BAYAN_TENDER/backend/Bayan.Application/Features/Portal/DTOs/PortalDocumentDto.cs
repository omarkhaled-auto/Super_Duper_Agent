namespace Bayan.Application.Features.Portal.DTOs;

/// <summary>
/// Data transfer object for documents displayed in the bidder portal.
/// </summary>
public class PortalDocumentDto
{
    /// <summary>
    /// Document unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Folder path within the tender (e.g., "RFP Package", "Drawings").
    /// </summary>
    public string FolderPath { get; set; } = string.Empty;

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSizeBytes { get; set; }

    /// <summary>
    /// Human-readable file size (e.g., "2.5 MB").
    /// </summary>
    public string FileSizeDisplay { get; set; } = string.Empty;

    /// <summary>
    /// MIME content type.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// Document version number.
    /// </summary>
    public int Version { get; set; }

    /// <summary>
    /// When the document was uploaded.
    /// </summary>
    public DateTime CreatedAt { get; set; }

    /// <summary>
    /// Whether this is the latest version.
    /// </summary>
    public bool IsLatest { get; set; }
}
