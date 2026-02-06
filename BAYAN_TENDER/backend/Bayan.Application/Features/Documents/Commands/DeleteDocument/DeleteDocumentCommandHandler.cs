using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Documents.Commands.DeleteDocument;

/// <summary>
/// Handler for the DeleteDocumentCommand.
/// </summary>
public class DeleteDocumentCommandHandler : IRequestHandler<DeleteDocumentCommand, bool>
{
    private readonly IApplicationDbContext _context;
    private readonly IFileStorageService _fileStorage;
    private readonly ILogger<DeleteDocumentCommandHandler> _logger;

    public DeleteDocumentCommandHandler(
        IApplicationDbContext context,
        IFileStorageService fileStorage,
        ILogger<DeleteDocumentCommandHandler> logger)
    {
        _context = context;
        _fileStorage = fileStorage;
        _logger = logger;
    }

    public async Task<bool> Handle(
        DeleteDocumentCommand request,
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
            return false;
        }

        var documentsToDelete = new List<Domain.Entities.Document> { document };

        // If deleting all versions, find all related documents
        if (request.DeleteAllVersions)
        {
            var baseFileName = GetBaseFileName(document.FileName);
            var allVersions = await _context.Documents
                .Where(d =>
                    d.TenderId == request.TenderId &&
                    d.FolderPath == document.FolderPath &&
                    d.FileName.StartsWith(baseFileName) &&
                    d.Id != document.Id)
                .ToListAsync(cancellationToken);

            documentsToDelete.AddRange(allVersions);
        }
        else if (document.IsLatest)
        {
            // If deleting the latest version, promote the previous version
            var previousVersion = await _context.Documents
                .Where(d =>
                    d.TenderId == request.TenderId &&
                    d.FolderPath == document.FolderPath &&
                    d.FileName.StartsWith(GetBaseFileName(document.FileName)) &&
                    d.Id != document.Id &&
                    !d.IsLatest)
                .OrderByDescending(d => d.Version)
                .FirstOrDefaultAsync(cancellationToken);

            if (previousVersion != null)
            {
                previousVersion.IsLatest = true;
            }
        }

        // Delete files from storage
        foreach (var doc in documentsToDelete)
        {
            try
            {
                await _fileStorage.DeleteFileAsync(doc.FilePath, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex,
                    "Failed to delete file from storage: {FilePath}. Document record will still be removed.",
                    doc.FilePath);
            }
        }

        // Remove document records from database
        _context.Documents.RemoveRange(documentsToDelete);
        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Deleted {Count} document(s) for tender {TenderId}",
            documentsToDelete.Count, request.TenderId);

        return true;
    }

    /// <summary>
    /// Gets the base file name without the timestamp suffix added during upload.
    /// </summary>
    private static string GetBaseFileName(string fileName)
    {
        var extension = Path.GetExtension(fileName);
        var nameWithoutExtension = Path.GetFileNameWithoutExtension(fileName);

        var lastUnderscore = nameWithoutExtension.LastIndexOf('_');
        if (lastUnderscore > 0)
        {
            var possibleTimestamp = nameWithoutExtension.Substring(lastUnderscore + 1);
            if (possibleTimestamp.Length == 17 && possibleTimestamp.All(char.IsDigit))
            {
                return nameWithoutExtension.Substring(0, lastUnderscore);
            }
        }

        return nameWithoutExtension;
    }
}
