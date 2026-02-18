using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Bids.Commands.UploadBidFile;

/// <summary>
/// Handler for the UploadBidFileCommand.
/// </summary>
public class UploadBidFileCommandHandler : IRequestHandler<UploadBidFileCommand, UploadBidFileResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IFileStorageService _fileStorage;
    private readonly IDateTime _dateTime;
    private readonly ILogger<UploadBidFileCommandHandler> _logger;

    public UploadBidFileCommandHandler(
        IApplicationDbContext context,
        IFileStorageService fileStorage,
        IDateTime dateTime,
        ILogger<UploadBidFileCommandHandler> logger)
    {
        _context = context;
        _fileStorage = fileStorage;
        _dateTime = dateTime;
        _logger = logger;
    }

    public async Task<UploadBidFileResultDto> Handle(
        UploadBidFileCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists and is accepting submissions
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        if (tender.Status != TenderStatus.Active)
        {
            throw new InvalidOperationException("Tender is not accepting bid submissions.");
        }

        // Verify bidder exists and is invited to this tender
        var bidder = await _context.Bidders
            .FirstOrDefaultAsync(b => b.Id == request.BidderId, cancellationToken);

        if (bidder == null)
        {
            throw new NotFoundException("Bidder", request.BidderId);
        }

        var isInvited = await _context.TenderBidders
            .AnyAsync(tb =>
                tb.TenderId == request.TenderId &&
                tb.BidderId == request.BidderId,
                cancellationToken);

        if (!isInvited)
        {
            throw new InvalidOperationException("Bidder is not invited to this tender.");
        }

        // Get or create a pending bid submission for this bidder/tender
        var bidSubmission = await _context.BidSubmissions
            .Include(b => b.BidDocuments)
            .FirstOrDefaultAsync(b =>
                b.TenderId == request.TenderId &&
                b.BidderId == request.BidderId &&
                b.Status == BidSubmissionStatus.Submitted &&
                b.ReceiptNumber == string.Empty, // Pending submission (not finalized)
                cancellationToken);

        if (bidSubmission == null)
        {
            // Create a new pending submission
            bidSubmission = new BidSubmission
            {
                Id = Guid.NewGuid(),
                TenderId = request.TenderId,
                BidderId = request.BidderId,
                SubmissionTime = _dateTime.UtcNow,
                Status = BidSubmissionStatus.Submitted,
                ReceiptNumber = string.Empty, // Will be set on final submission
                CreatedAt = _dateTime.UtcNow
            };

            _context.BidSubmissions.Add(bidSubmission);
        }

        // Check if there's already a document of this type - if so, replace it
        var existingDoc = bidSubmission.BidDocuments
            .FirstOrDefault(d => d.DocumentType == request.DocumentType);

        if (existingDoc != null)
        {
            // Delete the old file from storage
            try
            {
                await _fileStorage.DeleteFileAsync(existingDoc.FilePath, cancellationToken);
            }
            catch
            {
                // Ignore deletion errors - file may have already been deleted
            }

            // Remove the old document record
            _context.BidDocuments.Remove(existingDoc);
        }

        // Construct the storage path: bid-submissions/{tenderId}/{bidderId}/{documentType}/{filename}
        var documentTypeName = request.DocumentType.ToString();
        var storagePath = $"bid-submissions/{request.TenderId}/{request.BidderId}/{documentTypeName}";

        // Upload file to MinIO
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
            _logger.LogError(ex,
                "File upload failed for {FileName} on BidSubmission {BidSubmissionId}",
                request.FileName, bidSubmission.Id);
            throw new InvalidOperationException(
                $"Failed to upload file '{request.FileName}'. Please try again or contact support.", ex);
        }

        // Create bid document entity
        var bidDocument = new BidDocument
        {
            Id = Guid.NewGuid(),
            BidSubmissionId = bidSubmission.Id,
            DocumentType = request.DocumentType,
            FileName = request.FileName,
            FilePath = filePath,
            FileSizeBytes = request.FileSize,
            ContentType = request.ContentType,
            UploadedAt = _dateTime.UtcNow,
            CreatedAt = _dateTime.UtcNow
        };

        _context.BidDocuments.Add(bidDocument);

        // For PricedBOQ documents, set OriginalFilePath/OriginalFileName on the submission
        // so the bid import pipeline (parse → map → validate → execute) can find the file
        if (request.DocumentType == BidDocumentType.PricedBOQ)
        {
            bidSubmission.OriginalFilePath = filePath;
            bidSubmission.OriginalFileName = request.FileName;
            bidSubmission.ImportStatus = BidImportStatus.Uploaded;
        }

        await _context.SaveChangesAsync(cancellationToken);

        return new UploadBidFileResultDto
        {
            FileId = bidDocument.Id,
            DocumentType = bidDocument.DocumentType,
            FileName = bidDocument.FileName,
            FileSize = bidDocument.FileSizeBytes,
            FileSizeFormatted = FormatFileSize(bidDocument.FileSizeBytes),
            UploadedAt = bidDocument.UploadedAt
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
