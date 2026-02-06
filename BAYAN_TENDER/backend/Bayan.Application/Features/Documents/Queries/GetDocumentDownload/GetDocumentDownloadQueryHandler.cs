using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Documents.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Documents.Queries.GetDocumentDownload;

/// <summary>
/// Handler for the GetDocumentDownloadQuery.
/// </summary>
public class GetDocumentDownloadQueryHandler : IRequestHandler<GetDocumentDownloadQuery, DocumentDownloadDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IFileStorageService _fileStorage;

    /// <summary>
    /// Default URL expiry time (15 minutes).
    /// </summary>
    private static readonly TimeSpan UrlExpiry = TimeSpan.FromMinutes(15);

    public GetDocumentDownloadQueryHandler(
        IApplicationDbContext context,
        IFileStorageService fileStorage)
    {
        _context = context;
        _fileStorage = fileStorage;
    }

    public async Task<DocumentDownloadDto?> Handle(
        GetDocumentDownloadQuery request,
        CancellationToken cancellationToken)
    {
        // Find the document
        var document = await _context.Documents
            .FirstOrDefaultAsync(d =>
                d.Id == request.DocumentId &&
                d.TenderId == request.TenderId,
                cancellationToken);

        if (document == null)
        {
            return null;
        }

        // Generate presigned URL
        var downloadUrl = await _fileStorage.GetPresignedUrlAsync(
            document.FilePath,
            UrlExpiry,
            cancellationToken);

        return new DocumentDownloadDto
        {
            DocumentId = document.Id,
            FileName = document.FileName,
            ContentType = document.ContentType,
            DownloadUrl = downloadUrl,
            ExpiresAt = DateTime.UtcNow.Add(UrlExpiry)
        };
    }
}
