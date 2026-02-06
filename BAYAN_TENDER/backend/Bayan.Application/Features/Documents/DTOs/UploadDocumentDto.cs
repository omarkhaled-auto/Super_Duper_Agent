using Microsoft.AspNetCore.Http;

namespace Bayan.Application.Features.Documents.DTOs;

/// <summary>
/// Data transfer object for uploading a document.
/// </summary>
public class UploadDocumentDto
{
    /// <summary>
    /// The file to upload.
    /// </summary>
    public IFormFile File { get; set; } = null!;

    /// <summary>
    /// Folder path within the tender (e.g., "RFP Package", "Drawings").
    /// </summary>
    public string FolderPath { get; set; } = string.Empty;
}
