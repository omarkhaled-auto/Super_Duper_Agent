using Bayan.Application.Features.Boq.DTOs;
using MediatR;

namespace Bayan.Application.Features.Boq.Commands.UploadBoqImportFile;

/// <summary>
/// Command to upload an Excel file for BOQ import.
/// </summary>
public class UploadBoqImportFileCommand : IRequest<ExcelPreviewDto>
{
    /// <summary>
    /// ID of the tender to import BOQ data into.
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
}
