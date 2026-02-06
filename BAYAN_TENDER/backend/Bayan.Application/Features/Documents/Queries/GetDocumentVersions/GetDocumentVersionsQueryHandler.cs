using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Documents.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Documents.Queries.GetDocumentVersions;

/// <summary>
/// Handler for the GetDocumentVersionsQuery.
/// </summary>
public class GetDocumentVersionsQueryHandler : IRequestHandler<GetDocumentVersionsQuery, IReadOnlyList<DocumentDto>>
{
    private readonly IApplicationDbContext _context;

    public GetDocumentVersionsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<IReadOnlyList<DocumentDto>> Handle(
        GetDocumentVersionsQuery request,
        CancellationToken cancellationToken)
    {
        // First, find the document to get its file name and folder
        var document = await _context.Documents
            .FirstOrDefaultAsync(d =>
                d.Id == request.DocumentId &&
                d.TenderId == request.TenderId,
                cancellationToken);

        if (document == null)
        {
            return Array.Empty<DocumentDto>();
        }

        // Get the base file name (without timestamp suffix) to find all versions
        // Documents with the same original name in the same folder are considered versions
        var baseFileName = GetBaseFileName(document.FileName);

        // Find all versions of this document
        var versions = await _context.Documents
            .Include(d => d.Uploader)
            .Where(d =>
                d.TenderId == request.TenderId &&
                d.FolderPath == document.FolderPath &&
                d.FileName.StartsWith(baseFileName))
            .OrderByDescending(d => d.Version)
            .Select(d => new DocumentDto
            {
                Id = d.Id,
                TenderId = d.TenderId,
                Name = d.FileName,
                Folder = d.FolderPath,
                Size = d.FileSizeBytes,
                SizeFormatted = FormatFileSize(d.FileSizeBytes),
                ContentType = d.ContentType,
                Version = d.Version,
                IsLatest = d.IsLatest,
                UploadedAt = d.CreatedAt,
                UploadedBy = d.UploadedBy,
                UploadedByName = d.Uploader != null
                    ? $"{d.Uploader.FirstName} {d.Uploader.LastName}"
                    : "Unknown"
            })
            .ToListAsync(cancellationToken);

        return versions.AsReadOnly();
    }

    /// <summary>
    /// Gets the base file name without the timestamp suffix added during upload.
    /// </summary>
    private static string GetBaseFileName(string fileName)
    {
        // File names are stored as "originalname_timestamp.ext"
        // We need to extract the base name for version matching
        var extension = Path.GetExtension(fileName);
        var nameWithoutExtension = Path.GetFileNameWithoutExtension(fileName);

        // Find the last underscore followed by a timestamp pattern
        var lastUnderscore = nameWithoutExtension.LastIndexOf('_');
        if (lastUnderscore > 0)
        {
            var possibleTimestamp = nameWithoutExtension.Substring(lastUnderscore + 1);
            // Check if it looks like a timestamp (17 digits: yyyyMMddHHmmssfff)
            if (possibleTimestamp.Length == 17 && possibleTimestamp.All(char.IsDigit))
            {
                return nameWithoutExtension.Substring(0, lastUnderscore);
            }
        }

        return nameWithoutExtension;
    }

    /// <summary>
    /// Formats file size in human-readable format.
    /// </summary>
    private static string FormatFileSize(long bytes)
    {
        string[] sizes = { "B", "KB", "MB", "GB", "TB" };
        int order = 0;
        double size = bytes;

        while (size >= 1024 && order < sizes.Length - 1)
        {
            order++;
            size /= 1024;
        }

        return $"{size:0.##} {sizes[order]}";
    }
}
