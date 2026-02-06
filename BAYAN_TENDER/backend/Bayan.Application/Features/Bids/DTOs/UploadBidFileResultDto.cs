using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Result of uploading a bid file.
/// </summary>
public class UploadBidFileResultDto
{
    /// <summary>
    /// ID of the uploaded file.
    /// </summary>
    public Guid FileId { get; set; }

    /// <summary>
    /// Type of document.
    /// </summary>
    public BidDocumentType DocumentType { get; set; }

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSize { get; set; }

    /// <summary>
    /// File size formatted for display.
    /// </summary>
    public string FileSizeFormatted { get; set; } = string.Empty;

    /// <summary>
    /// When the file was uploaded.
    /// </summary>
    public DateTime UploadedAt { get; set; }
}
