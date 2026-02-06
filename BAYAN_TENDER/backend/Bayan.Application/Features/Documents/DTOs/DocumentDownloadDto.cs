namespace Bayan.Application.Features.Documents.DTOs;

/// <summary>
/// Data transfer object for document download response.
/// </summary>
public class DocumentDownloadDto
{
    /// <summary>
    /// Document ID.
    /// </summary>
    public Guid DocumentId { get; set; }

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// MIME content type.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// Presigned URL for downloading the file.
    /// </summary>
    public string DownloadUrl { get; set; } = string.Empty;

    /// <summary>
    /// When the presigned URL expires.
    /// </summary>
    public DateTime ExpiresAt { get; set; }
}
