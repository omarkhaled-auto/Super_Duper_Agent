using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Clarifications.Queries.DownloadBulletin;

/// <summary>
/// Handler for the DownloadBulletinQuery.
/// </summary>
public class DownloadBulletinQueryHandler : IRequestHandler<DownloadBulletinQuery, BulletinDownloadDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IFileStorageService _fileStorageService;
    private readonly IPdfService _pdfService;
    private readonly ILogger<DownloadBulletinQueryHandler> _logger;

    public DownloadBulletinQueryHandler(
        IApplicationDbContext context,
        IFileStorageService fileStorageService,
        IPdfService pdfService,
        ILogger<DownloadBulletinQueryHandler> logger)
    {
        _context = context;
        _fileStorageService = fileStorageService;
        _pdfService = pdfService;
        _logger = logger;
    }

    public async Task<BulletinDownloadDto?> Handle(
        DownloadBulletinQuery request,
        CancellationToken cancellationToken)
    {
        // Get the bulletin with related data
        var bulletin = await _context.ClarificationBulletins
            .Include(b => b.Tender)
            .Include(b => b.Clarifications)
            .FirstOrDefaultAsync(
                b => b.Id == request.BulletinId && b.TenderId == request.TenderId,
                cancellationToken);

        if (bulletin == null)
        {
            return null;
        }

        var bulletinReference = $"QB-{bulletin.BulletinNumber:D3}";
        var fileName = $"{bulletin.Tender.Reference}_{bulletinReference}.pdf";

        byte[] pdfContent;

        // Try to get from storage first
        if (!string.IsNullOrEmpty(bulletin.PdfPath))
        {
            try
            {
                using var stream = await _fileStorageService.DownloadFileAsync(
                    bulletin.PdfPath, cancellationToken);

                using var memoryStream = new MemoryStream();
                await stream.CopyToAsync(memoryStream, cancellationToken);
                pdfContent = memoryStream.ToArray();

                _logger.LogDebug(
                    "Downloaded bulletin PDF from storage: {Path}",
                    bulletin.PdfPath);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex,
                    "Failed to download bulletin PDF from storage, regenerating. Path: {Path}",
                    bulletin.PdfPath);

                // Regenerate the PDF if storage retrieval fails
                pdfContent = await _pdfService.GenerateBulletinPdfAsync(
                    bulletin,
                    bulletin.Tender,
                    bulletin.Clarifications,
                    cancellationToken);
            }
        }
        else
        {
            // Generate PDF on the fly if no stored path
            _logger.LogInformation(
                "No stored PDF path for bulletin {BulletinId}, generating...",
                request.BulletinId);

            pdfContent = await _pdfService.GenerateBulletinPdfAsync(
                bulletin,
                bulletin.Tender,
                bulletin.Clarifications,
                cancellationToken);
        }

        return new BulletinDownloadDto
        {
            Content = pdfContent,
            FileName = fileName,
            ContentType = "application/pdf"
        };
    }
}
