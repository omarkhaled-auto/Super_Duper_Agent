namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for downloading a bulletin PDF.
/// </summary>
public class BulletinDownloadDto
{
    /// <summary>
    /// The PDF file content.
    /// </summary>
    public byte[] Content { get; set; } = Array.Empty<byte>();

    /// <summary>
    /// The file name for the download.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// The content type (MIME type).
    /// </summary>
    public string ContentType { get; set; } = "application/pdf";
}
