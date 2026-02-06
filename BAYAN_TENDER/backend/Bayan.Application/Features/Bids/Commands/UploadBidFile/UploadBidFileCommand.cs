using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Bids.Commands.UploadBidFile;

/// <summary>
/// Command to upload a file for a bid submission.
/// </summary>
public class UploadBidFileCommand : IRequest<UploadBidFileResultDto>
{
    /// <summary>
    /// ID of the tender to upload the file for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the bidder uploading the file.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Type of bid document.
    /// </summary>
    public BidDocumentType DocumentType { get; set; }

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
