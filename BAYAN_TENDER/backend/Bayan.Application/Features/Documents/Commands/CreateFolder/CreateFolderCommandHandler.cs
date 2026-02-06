using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Documents.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Documents.Commands.CreateFolder;

/// <summary>
/// Handler for the CreateFolderCommand.
/// Folders are virtual in this system - this validates the folder and returns its info.
/// </summary>
public class CreateFolderCommandHandler : IRequestHandler<CreateFolderCommand, FolderDto>
{
    private readonly IApplicationDbContext _context;

    public CreateFolderCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<FolderDto> Handle(
        CreateFolderCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists
        var tenderExists = await _context.Tenders
            .AnyAsync(t => t.Id == request.TenderId, cancellationToken);

        if (!tenderExists)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        // Construct the full folder path
        var folderPath = string.IsNullOrWhiteSpace(request.ParentPath)
            ? request.FolderName
            : $"{request.ParentPath.TrimEnd('/')}/{request.FolderName}";

        // Check if folder already has documents
        var folderStats = await _context.Documents
            .Where(d =>
                d.TenderId == request.TenderId &&
                d.FolderPath == folderPath &&
                d.IsLatest)
            .GroupBy(d => d.FolderPath)
            .Select(g => new
            {
                DocumentCount = g.Count(),
                TotalSize = g.Sum(d => d.FileSizeBytes),
                LastModified = g.Max(d => d.CreatedAt)
            })
            .FirstOrDefaultAsync(cancellationToken);

        return new FolderDto
        {
            Name = request.FolderName,
            Path = folderPath,
            DocumentCount = folderStats?.DocumentCount ?? 0,
            TotalSize = folderStats?.TotalSize ?? 0,
            TotalSizeFormatted = FormatFileSize(folderStats?.TotalSize ?? 0),
            CreatedAt = DateTime.UtcNow,
            LastModifiedAt = folderStats?.LastModified
        };
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
