using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Documents.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Documents.Queries.GetFolders;

/// <summary>
/// Handler for the GetFoldersQuery.
/// </summary>
public class GetFoldersQueryHandler : IRequestHandler<GetFoldersQuery, IReadOnlyList<FolderDto>>
{
    private readonly IApplicationDbContext _context;

    /// <summary>
    /// Default folders for tender documents.
    /// </summary>
    public static readonly IReadOnlyList<string> DefaultFolders = new[]
    {
        "RFP Package",
        "Drawings",
        "Specifications",
        "BOQ",
        "Contract Forms",
        "Addenda",
        "Clarifications"
    };

    public GetFoldersQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<IReadOnlyList<FolderDto>> Handle(
        GetFoldersQuery request,
        CancellationToken cancellationToken)
    {
        // Get all documents for the tender grouped by folder
        var folderStats = await _context.Documents
            .Where(d => d.TenderId == request.TenderId && d.IsLatest)
            .GroupBy(d => d.FolderPath)
            .Select(g => new
            {
                FolderPath = g.Key,
                DocumentCount = g.Count(),
                TotalSize = g.Sum(d => d.FileSizeBytes),
                LastModified = g.Max(d => d.CreatedAt)
            })
            .ToDictionaryAsync(x => x.FolderPath, cancellationToken);

        // Combine default folders with any custom folders that have documents
        var allFolders = DefaultFolders
            .Concat(folderStats.Keys.Where(k => !DefaultFolders.Contains(k)))
            .Distinct()
            .OrderBy(f => DefaultFolders.Contains(f) ? DefaultFolders.ToList().IndexOf(f) : int.MaxValue)
            .ThenBy(f => f)
            .ToList();

        var result = allFolders.Select(folder =>
        {
            var stats = folderStats.GetValueOrDefault(folder);
            return new FolderDto
            {
                Name = folder,
                Path = folder,
                DocumentCount = stats?.DocumentCount ?? 0,
                TotalSize = stats?.TotalSize ?? 0,
                TotalSizeFormatted = FormatFileSize(stats?.TotalSize ?? 0),
                CreatedAt = DateTime.UtcNow, // Folders are virtual, use current time
                LastModifiedAt = stats?.LastModified
            };
        }).ToList();

        return result.AsReadOnly();
    }

    /// <summary>
    /// Formats file size in human-readable format.
    /// </summary>
    private static string FormatFileSize(long bytes)
    {
        if (bytes == 0) return "0 B";

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
