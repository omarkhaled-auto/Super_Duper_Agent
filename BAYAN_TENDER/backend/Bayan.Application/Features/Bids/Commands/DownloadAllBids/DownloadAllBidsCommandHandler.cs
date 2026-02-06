using System.IO.Compression;
using System.Text.RegularExpressions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.DownloadAllBids;

/// <summary>
/// Handler for the DownloadAllBidsCommand.
/// Creates a ZIP file with all bid documents organized by bidder.
/// </summary>
public class DownloadAllBidsCommandHandler : IRequestHandler<DownloadAllBidsCommand, DownloadAllBidsResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IFileStorageService _fileStorageService;
    private readonly ICurrentUserService _currentUserService;

    public DownloadAllBidsCommandHandler(
        IApplicationDbContext context,
        IFileStorageService fileStorageService,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _fileStorageService = fileStorageService;
        _currentUserService = currentUserService;
    }

    public async Task<DownloadAllBidsResultDto> Handle(
        DownloadAllBidsCommand request,
        CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new InvalidOperationException($"Tender with ID {request.TenderId} not found.");
        }

        // Get all bids with their documents
        var bids = await _context.BidSubmissions
            .Include(b => b.Bidder)
            .Include(b => b.BidDocuments)
            .Where(b => b.TenderId == request.TenderId)
            .ToListAsync(cancellationToken);

        if (!bids.Any())
        {
            throw new InvalidOperationException("No bids found for this tender.");
        }

        var generatedAt = DateTime.UtcNow;
        var requestedBy = _currentUserService.UserId ?? Guid.Empty;

        // Create the ZIP file in memory
        using var memoryStream = new MemoryStream();
        using (var archive = new ZipArchive(memoryStream, ZipArchiveMode.Create, true))
        {
            foreach (var bid in bids)
            {
                var bidderFolderName = SanitizeFolderName(bid.Bidder.CompanyName);

                foreach (var doc in bid.BidDocuments)
                {
                    // Determine if document is Commercial or Technical
                    var category = doc.DocumentType == BidDocumentType.PricedBOQ
                        ? "Commercial"
                        : "Technical";

                    var entryPath = $"{bidderFolderName}/{category}/{doc.FileName}";

                    try
                    {
                        // Download the file from storage
                        using var fileStream = await _fileStorageService.DownloadFileAsync(
                            doc.FilePath,
                            cancellationToken);

                        // Create entry in ZIP
                        var entry = archive.CreateEntry(entryPath, CompressionLevel.Optimal);
                        using var entryStream = entry.Open();
                        await fileStream.CopyToAsync(entryStream, cancellationToken);
                    }
                    catch
                    {
                        // If file download fails, create a placeholder entry
                        var entry = archive.CreateEntry($"{entryPath}.missing.txt", CompressionLevel.Optimal);
                        using var entryStream = entry.Open();
                        using var writer = new StreamWriter(entryStream);
                        await writer.WriteLineAsync($"File not found: {doc.FileName}");
                        await writer.WriteLineAsync($"Original path: {doc.FilePath}");
                    }
                }

                // Add original bid file if exists
                if (!string.IsNullOrEmpty(bid.OriginalFilePath) && !string.IsNullOrEmpty(bid.OriginalFileName))
                {
                    try
                    {
                        using var fileStream = await _fileStorageService.DownloadFileAsync(
                            bid.OriginalFilePath,
                            cancellationToken);

                        var entry = archive.CreateEntry($"{bidderFolderName}/{bid.OriginalFileName}", CompressionLevel.Optimal);
                        using var entryStream = entry.Open();
                        await fileStream.CopyToAsync(entryStream, cancellationToken);
                    }
                    catch
                    {
                        // Ignore if original file not found
                    }
                }
            }

            // Add a summary file
            var summaryEntry = archive.CreateEntry("_SUMMARY.txt", CompressionLevel.Optimal);
            using var summaryStream = summaryEntry.Open();
            using var summaryWriter = new StreamWriter(summaryStream);
            await summaryWriter.WriteLineAsync($"Tender: {tender.Title}");
            await summaryWriter.WriteLineAsync($"Reference: {tender.Reference}");
            await summaryWriter.WriteLineAsync($"Generated: {generatedAt:yyyy-MM-dd HH:mm:ss} UTC");
            await summaryWriter.WriteLineAsync($"Total Bids: {bids.Count}");
            await summaryWriter.WriteLineAsync();
            await summaryWriter.WriteLineAsync("Bidders:");
            foreach (var bid in bids.OrderBy(b => b.Bidder.CompanyName))
            {
                await summaryWriter.WriteLineAsync($"  - {bid.Bidder.CompanyName} ({bid.BidDocuments.Count} documents)");
            }
        }

        // Reset stream position
        memoryStream.Position = 0;

        // Generate file name
        var sanitizedReference = SanitizeFolderName(tender.Reference);
        var fileName = $"{sanitizedReference}_AllBids_{generatedAt:yyyyMMdd_HHmmss}.zip";

        // Upload ZIP to storage
        var zipPath = await _fileStorageService.UploadFileAsync(
            memoryStream,
            fileName,
            "application/zip",
            $"tender-downloads/{request.TenderId}",
            cancellationToken);

        // Generate presigned URL (valid for 1 hour)
        var downloadUrl = await _fileStorageService.GetPresignedUrlAsync(
            zipPath,
            TimeSpan.FromHours(1),
            cancellationToken);

        return new DownloadAllBidsResultDto
        {
            TenderId = request.TenderId,
            TenderReference = tender.Reference,
            DownloadUrl = downloadUrl,
            UrlExpiresAt = generatedAt.AddHours(1),
            FileName = fileName,
            FileSizeBytes = memoryStream.Length,
            BidCount = bids.Count,
            DocumentCount = bids.Sum(b => b.BidDocuments.Count),
            GeneratedAt = generatedAt,
            RequestedBy = requestedBy
        };
    }

    /// <summary>
    /// Sanitizes a string to be safe for use as a folder name.
    /// </summary>
    private static string SanitizeFolderName(string name)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            return "Unknown";
        }

        // Remove invalid characters
        var invalidChars = Path.GetInvalidFileNameChars();
        var sanitized = new string(name.Where(c => !invalidChars.Contains(c)).ToArray());

        // Replace spaces with underscores
        sanitized = sanitized.Replace(' ', '_');

        // Remove consecutive underscores
        sanitized = Regex.Replace(sanitized, "_+", "_");

        // Trim underscores from start and end
        sanitized = sanitized.Trim('_');

        // Ensure not empty
        if (string.IsNullOrWhiteSpace(sanitized))
        {
            sanitized = "Unknown";
        }

        // Limit length
        if (sanitized.Length > 100)
        {
            sanitized = sanitized.Substring(0, 100);
        }

        return sanitized;
    }
}
