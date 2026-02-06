using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Queries.GetBidDetails;

/// <summary>
/// Handler for the GetBidDetailsQuery.
/// </summary>
public class GetBidDetailsQueryHandler : IRequestHandler<GetBidDetailsQuery, BidDetailDto?>
{
    private readonly IApplicationDbContext _context;

    public GetBidDetailsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<BidDetailDto?> Handle(
        GetBidDetailsQuery request,
        CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .Include(b => b.Tender)
            .Include(b => b.Bidder)
            .Include(b => b.BidDocuments)
            .Include(b => b.LateAcceptedByUser)
            .Include(b => b.Importer)
            .Where(b => b.Id == request.BidId && b.TenderId == request.TenderId)
            .AsNoTracking()
            .FirstOrDefaultAsync(cancellationToken);

        if (bid == null)
        {
            return null;
        }

        var isOpened = bid.Status == BidSubmissionStatus.Opened ||
                      bid.Status == BidSubmissionStatus.Imported ||
                      bid.Status == BidSubmissionStatus.Disqualified;

        return new BidDetailDto
        {
            Id = bid.Id,
            TenderId = bid.TenderId,
            TenderReference = bid.Tender.Reference,
            TenderTitle = bid.Tender.Title,
            BidderId = bid.BidderId,
            BidderName = bid.Bidder.CompanyName,
            ContactPerson = bid.Bidder.ContactPerson,
            BidderEmail = bid.Bidder.Email,
            BidderPhone = bid.Bidder.Phone,
            CRNumber = bid.Bidder.CRNumber,
            SubmissionTime = bid.SubmissionTime,
            Status = bid.Status,
            IsLate = bid.IsLate,
            LateAccepted = bid.LateAccepted,
            LateAcceptedBy = bid.LateAcceptedBy,
            LateAcceptedByName = bid.LateAcceptedByUser != null
                ? $"{bid.LateAcceptedByUser.FirstName} {bid.LateAcceptedByUser.LastName}"
                : null,
            ReceiptNumber = bid.ReceiptNumber,
            ReceiptPdfPath = bid.ReceiptPdfPath,
            OriginalFileName = bid.OriginalFileName,
            NativeCurrency = bid.NativeCurrency,
            // Only show amounts if bids are opened
            NativeTotalAmount = isOpened ? bid.NativeTotalAmount : null,
            FxRate = bid.FxRate,
            NormalizedTotalAmount = isOpened ? bid.NormalizedTotalAmount : null,
            BidValidityDays = bid.BidValidityDays,
            ImportStatus = bid.ImportStatus,
            ImportStartedAt = bid.ImportStartedAt,
            ImportCompletedAt = bid.ImportCompletedAt,
            ImportedBy = bid.ImportedBy,
            ImportedByName = bid.Importer != null
                ? $"{bid.Importer.FirstName} {bid.Importer.LastName}"
                : null,
            ValidationSummary = bid.ValidationSummary,
            CreatedAt = bid.CreatedAt,
            Documents = bid.BidDocuments.Select(d => new BidDocumentDto
            {
                Id = d.Id,
                DocumentType = d.DocumentType,
                DocumentTypeName = GetDocumentTypeName(d.DocumentType),
                FileName = d.FileName,
                FileSizeBytes = d.FileSizeBytes,
                ContentType = d.ContentType,
                UploadedAt = d.UploadedAt,
                Category = GetDocumentCategory(d.DocumentType)
            }).OrderBy(d => d.Category).ThenBy(d => d.DocumentTypeName).ToList()
        };
    }

    private static string GetDocumentTypeName(BidDocumentType documentType)
    {
        return documentType switch
        {
            BidDocumentType.PricedBOQ => "Priced Bill of Quantities",
            BidDocumentType.Methodology => "Methodology",
            BidDocumentType.TeamCVs => "Team CVs",
            BidDocumentType.Program => "Project Program/Schedule",
            BidDocumentType.HSEPlan => "HSE Plan",
            BidDocumentType.Supporting => "Supporting Documents",
            _ => documentType.ToString()
        };
    }

    private static string GetDocumentCategory(BidDocumentType documentType)
    {
        return documentType switch
        {
            BidDocumentType.PricedBOQ => "Commercial",
            _ => "Technical"
        };
    }
}
