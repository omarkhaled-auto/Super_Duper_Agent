using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Documents.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Documents.Queries.GetDocuments;

/// <summary>
/// Handler for the GetDocumentsQuery.
/// </summary>
public class GetDocumentsQueryHandler : IRequestHandler<GetDocumentsQuery, PaginatedList<DocumentDto>>
{
    private readonly IApplicationDbContext _context;

    public GetDocumentsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<PaginatedList<DocumentDto>> Handle(
        GetDocumentsQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.Documents
            .Include(d => d.Uploader)
            .Where(d => d.TenderId == request.TenderId)
            .AsQueryable();

        // Filter by folder if specified
        if (!string.IsNullOrWhiteSpace(request.FolderPath))
        {
            query = query.Where(d => d.FolderPath == request.FolderPath);
        }

        // Filter by latest version if specified
        if (request.LatestOnly)
        {
            query = query.Where(d => d.IsLatest);
        }

        // Search by file name
        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchLower = request.Search.ToLower();
            query = query.Where(d => d.FileName.ToLower().Contains(searchLower));
        }

        // Order by upload date descending
        query = query.OrderByDescending(d => d.CreatedAt);

        // Get total count
        var totalCount = await query.CountAsync(cancellationToken);

        // Apply pagination
        var items = await query
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
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

        return new PaginatedList<DocumentDto>(
            items,
            totalCount,
            request.Page,
            request.PageSize);
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
