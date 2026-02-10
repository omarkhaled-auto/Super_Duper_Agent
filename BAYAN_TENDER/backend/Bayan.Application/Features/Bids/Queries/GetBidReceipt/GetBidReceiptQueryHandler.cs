using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Queries.GetBidReceipt;

/// <summary>
/// Handler for the GetBidReceiptQuery.
/// </summary>
public class GetBidReceiptQueryHandler : IRequestHandler<GetBidReceiptQuery, BidReceiptDto?>
{
    private readonly IApplicationDbContext _context;

    public GetBidReceiptQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<BidReceiptDto?> Handle(
        GetBidReceiptQuery request,
        CancellationToken cancellationToken)
    {
        var bidSubmission = await _context.BidSubmissions
            .Include(b => b.Tender)
            .Include(b => b.Bidder)
            .Include(b => b.BidDocuments)
            .FirstOrDefaultAsync(b =>
                b.Id == request.BidId &&
                b.BidderId == request.BidderId &&
                b.ReceiptNumber != string.Empty, // Only finalized submissions
                cancellationToken);

        if (bidSubmission == null)
        {
            return null;
        }

        return new BidReceiptDto
        {
            ReceiptNumber = bidSubmission.ReceiptNumber,
            BidId = bidSubmission.Id,
            TenderId = bidSubmission.TenderId,
            TenderTitle = bidSubmission.Tender.Title,
            TenderReference = bidSubmission.Tender.Reference,
            SubmittedAt = bidSubmission.SubmissionTime,
            Timezone = "UTC",
            BidderCompanyName = bidSubmission.Bidder.CompanyName,
            BidderEmail = bidSubmission.Bidder.Email,
            IsLate = bidSubmission.IsLate,
            Files = bidSubmission.BidDocuments.Select(d => new BidReceiptFileDto
            {
                DocumentType = d.DocumentType.ToString(),
                FileName = d.FileName,
                FileSizeBytes = d.FileSizeBytes,
                FileSizeFormatted = FormatFileSize(d.FileSizeBytes)
            }).ToList()
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
