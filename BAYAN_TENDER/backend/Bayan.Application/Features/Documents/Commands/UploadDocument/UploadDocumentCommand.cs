using Bayan.Application.Features.Documents.DTOs;
using MediatR;

namespace Bayan.Application.Features.Documents.Commands.UploadDocument;

/// <summary>
/// Command to upload a document to a tender.
/// </summary>
public class UploadDocumentCommand : IRequest<DocumentDto>
{
    /// <summary>
    /// ID of the tender to upload the document to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// File content stream.
    /// </summary>
    public Stream FileStream { get; set; } = null!;

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// MIME content type.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSize { get; set; }

    /// <summary>
    /// Folder path within the tender.
    /// </summary>
    public string FolderPath { get; set; } = string.Empty;
}
