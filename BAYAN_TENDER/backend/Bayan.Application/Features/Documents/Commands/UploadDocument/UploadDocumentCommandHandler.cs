using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Documents.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Documents.Commands.UploadDocument;

/// <summary>
/// Handler for the UploadDocumentCommand.
/// </summary>
public class UploadDocumentCommandHandler : IRequestHandler<UploadDocumentCommand, DocumentDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IFileStorageService _fileStorage;
    private readonly ICurrentUserService _currentUser;
    private readonly ILogger<UploadDocumentCommandHandler> _logger;

    public UploadDocumentCommandHandler(
        IApplicationDbContext context,
        IFileStorageService fileStorage,
        ICurrentUserService currentUser,
        ILogger<UploadDocumentCommandHandler> logger)
    {
        _context = context;
        _fileStorage = fileStorage;
        _currentUser = currentUser;
        _logger = logger;
    }

    public async Task<DocumentDto> Handle(
        UploadDocumentCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists
        var tenderExists = await _context.Tenders
            .AnyAsync(t => t.Id == request.TenderId, cancellationToken);

        if (!tenderExists)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        // Determine version number by checking for existing documents with the same name
        var existingVersion = await _context.Documents
            .Where(d =>
                d.TenderId == request.TenderId &&
                d.FolderPath == request.FolderPath &&
                d.FileName.StartsWith(Path.GetFileNameWithoutExtension(request.FileName)) &&
                d.IsLatest)
            .MaxAsync(d => (int?)d.Version, cancellationToken) ?? 0;

        var newVersion = existingVersion + 1;

        // Mark previous version as not latest
        if (existingVersion > 0)
        {
            var previousDocuments = await _context.Documents
                .Where(d =>
                    d.TenderId == request.TenderId &&
                    d.FolderPath == request.FolderPath &&
                    d.FileName.StartsWith(Path.GetFileNameWithoutExtension(request.FileName)) &&
                    d.IsLatest)
                .ToListAsync(cancellationToken);

            foreach (var doc in previousDocuments)
            {
                doc.IsLatest = false;
            }
        }

        // Construct the storage path: tender-documents/{tenderId}/{folder}
        var storagePath = $"{request.TenderId}/{request.FolderPath}";

        // Upload file to storage
        string filePath;
        try
        {
            filePath = await _fileStorage.UploadFileAsync(
                request.FileStream,
                request.FileName,
                request.ContentType,
                storagePath,
                cancellationToken);
        }
        catch (IOException ex)
        {
            _logger.LogError(ex, "File storage I/O error uploading {FileName} for tender {TenderId}",
                request.FileName, request.TenderId);
            throw new InvalidOperationException(
                $"Failed to upload file '{request.FileName}'. Please try again later.", ex);
        }

        // Create document entity
        var document = new Document
        {
            Id = Guid.NewGuid(),
            TenderId = request.TenderId,
            FolderPath = request.FolderPath,
            FileName = request.FileName,
            FilePath = filePath,
            FileSizeBytes = request.FileSize,
            ContentType = request.ContentType,
            Version = newVersion,
            IsLatest = true,
            UploadedBy = _currentUser.UserId ?? Guid.Empty,
            CreatedAt = DateTime.UtcNow
        };

        _context.Documents.Add(document);
        await _context.SaveChangesAsync(cancellationToken);

        // Get uploader name
        var uploaderName = "Unknown";
        if (_currentUser.UserId.HasValue)
        {
            var user = await _context.Users
                .FirstOrDefaultAsync(u => u.Id == _currentUser.UserId.Value, cancellationToken);

            if (user != null)
            {
                uploaderName = $"{user.FirstName} {user.LastName}";
            }
        }

        return new DocumentDto
        {
            Id = document.Id,
            TenderId = document.TenderId,
            Name = document.FileName,
            Folder = document.FolderPath,
            Size = document.FileSizeBytes,
            SizeFormatted = FormatFileSize(document.FileSizeBytes),
            ContentType = document.ContentType,
            Version = document.Version,
            IsLatest = document.IsLatest,
            UploadedAt = document.CreatedAt,
            UploadedBy = document.UploadedBy,
            UploadedByName = uploaderName
        };
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
