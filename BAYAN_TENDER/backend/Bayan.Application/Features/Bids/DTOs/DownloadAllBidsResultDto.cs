namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Data transfer object for download all bids result.
/// </summary>
public class DownloadAllBidsResultDto
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Reference number of the tender.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Presigned URL to download the ZIP file.
    /// </summary>
    public string DownloadUrl { get; set; } = string.Empty;

    /// <summary>
    /// When the URL expires.
    /// </summary>
    public DateTime UrlExpiresAt { get; set; }

    /// <summary>
    /// Name of the ZIP file.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Size of the ZIP file in bytes.
    /// </summary>
    public long FileSizeBytes { get; set; }

    /// <summary>
    /// Number of bids included in the ZIP.
    /// </summary>
    public int BidCount { get; set; }

    /// <summary>
    /// Total number of documents included.
    /// </summary>
    public int DocumentCount { get; set; }

    /// <summary>
    /// Timestamp when the ZIP was generated.
    /// </summary>
    public DateTime GeneratedAt { get; set; }

    /// <summary>
    /// User who requested the download.
    /// </summary>
    public Guid RequestedBy { get; set; }
}
