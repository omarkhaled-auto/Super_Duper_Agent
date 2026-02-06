using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetBidderTechnicalDocuments;

/// <summary>
/// Handler for GetBidderTechnicalDocumentsQuery.
/// </summary>
public class GetBidderTechnicalDocumentsQueryHandler
    : IRequestHandler<GetBidderTechnicalDocumentsQuery, BidderTechnicalDocumentsDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public GetBidderTechnicalDocumentsQueryHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<BidderTechnicalDocumentsDto?> Handle(
        GetBidderTechnicalDocumentsQuery request,
        CancellationToken cancellationToken)
    {
        var currentUserId = _currentUserService.UserId;
        if (currentUserId == null)
        {
            return null;
        }

        // Verify user is a panelist for this tender
        var isPanelist = await _context.EvaluationPanels
            .AnyAsync(p => p.TenderId == request.TenderId &&
                         p.PanelistUserId == currentUserId.Value,
                     cancellationToken);

        if (!isPanelist)
        {
            return null;
        }

        // Get evaluation state to check blind mode
        var evaluationState = await _context.EvaluationStates
            .AsNoTracking()
            .FirstOrDefaultAsync(e => e.TenderId == request.TenderId, cancellationToken);

        var blindMode = evaluationState?.BlindMode ?? true;

        // Get bid submission with documents
        var submission = await _context.BidSubmissions
            .Include(b => b.Bidder)
            .Include(b => b.BidDocuments)
            .AsNoTracking()
            .FirstOrDefaultAsync(b => b.TenderId == request.TenderId &&
                                     b.BidderId == request.BidderId,
                                 cancellationToken);

        if (submission == null)
        {
            return null;
        }

        // Generate anonymous ID
        var allBidderIds = await _context.BidSubmissions
            .Where(b => b.TenderId == request.TenderId)
            .OrderBy(b => b.BidderId)
            .Select(b => b.BidderId)
            .ToListAsync(cancellationToken);

        var bidderIndex = allBidderIds.IndexOf(request.BidderId) + 1;
        var anonymousId = $"Bidder {bidderIndex:D3}";

        // Filter to technical documents only (methodology, team CVs, program, HSE plan, supporting docs)
        // Note: PricedBOQ is excluded as it's for commercial evaluation
        var technicalDocumentTypes = new[]
        {
            BidDocumentType.Methodology,
            BidDocumentType.TeamCVs,
            BidDocumentType.Program,
            BidDocumentType.HSEPlan,
            BidDocumentType.Supporting
        };

        var documents = submission.BidDocuments
            .Where(d => technicalDocumentTypes.Contains(d.DocumentType))
            .Select(d => new BidderTechnicalDocumentDto
            {
                Id = d.Id,
                DocumentType = d.DocumentType.ToString(),
                FileName = blindMode ? SanitizeFileName(d.FileName, anonymousId) : d.FileName,
                FileSizeBytes = d.FileSizeBytes,
                ContentType = d.ContentType,
                UploadedAt = d.UploadedAt,
                DownloadUrl = $"/api/tenders/{request.TenderId}/evaluation/documents/{d.Id}"
            })
            .ToList();

        return new BidderTechnicalDocumentsDto
        {
            BidderId = request.BidderId,
            CompanyName = blindMode ? null : submission.Bidder.CompanyName,
            AnonymousId = anonymousId,
            BlindMode = blindMode,
            Documents = documents
        };
    }

    /// <summary>
    /// Sanitizes file names in blind mode to remove bidder identifying information.
    /// </summary>
    private static string SanitizeFileName(string fileName, string anonymousId)
    {
        // Remove company names or identifying info from file names
        // Keep the extension and add anonymous prefix
        var extension = Path.GetExtension(fileName);
        var baseName = Path.GetFileNameWithoutExtension(fileName);

        // If file name might contain identifying info, replace it
        // This is a simple implementation - could be more sophisticated
        if (baseName.Length > 20)
        {
            var truncated = baseName.Substring(0, 20);
            return $"{anonymousId}_{truncated}{extension}";
        }

        return $"{anonymousId}_{baseName}{extension}";
    }
}
