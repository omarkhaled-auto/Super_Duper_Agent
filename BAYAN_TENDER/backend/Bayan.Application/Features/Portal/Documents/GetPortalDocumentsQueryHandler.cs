using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Documents;

/// <summary>
/// Handler for GetPortalDocumentsQuery.
/// </summary>
public class GetPortalDocumentsQueryHandler : IRequestHandler<GetPortalDocumentsQuery, List<PortalDocumentDto>>
{
    private readonly IApplicationDbContext _context;

    public GetPortalDocumentsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<PortalDocumentDto>> Handle(GetPortalDocumentsQuery request, CancellationToken cancellationToken)
    {
        // Validate bidder access to tender
        var tenderBidder = await _context.TenderBidders
            .FirstOrDefaultAsync(tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId, cancellationToken);

        if (tenderBidder == null)
        {
            throw new UnauthorizedAccessException("You do not have access to this tender.");
        }

        if (tenderBidder.QualificationStatus != QualificationStatus.Qualified)
        {
            throw new UnauthorizedAccessException($"You are not qualified for this tender. Current status: {tenderBidder.QualificationStatus}");
        }

        // Get documents (only latest versions)
        var query = _context.Documents
            .Where(d => d.TenderId == request.TenderId && d.IsLatest);

        if (!string.IsNullOrEmpty(request.FolderPath))
        {
            query = query.Where(d => d.FolderPath == request.FolderPath);
        }

        var documents = await query
            .OrderBy(d => d.FolderPath)
            .ThenBy(d => d.FileName)
            .Select(d => new PortalDocumentDto
            {
                Id = d.Id,
                FolderPath = d.FolderPath,
                FileName = d.FileName,
                FileSizeBytes = d.FileSizeBytes,
                FileSizeDisplay = FormatFileSize(d.FileSizeBytes),
                ContentType = d.ContentType,
                Version = d.Version,
                CreatedAt = d.CreatedAt,
                IsLatest = d.IsLatest
            })
            .ToListAsync(cancellationToken);

        return documents;
    }

    private static string FormatFileSize(long bytes)
    {
        string[] sizes = { "B", "KB", "MB", "GB", "TB" };
        double len = bytes;
        int order = 0;
        while (len >= 1024 && order < sizes.Length - 1)
        {
            order++;
            len /= 1024;
        }
        return $"{len:0.##} {sizes[order]}";
    }
}
