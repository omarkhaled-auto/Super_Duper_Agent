using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.Commands.GenerateBidReceiptPdf;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.SubmitBid;

/// <summary>
/// Handler for the SubmitBidCommand.
/// </summary>
public class SubmitBidCommandHandler : IRequestHandler<SubmitBidCommand, SubmitBidResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMediator _mediator;
    private readonly IEmailService _emailService;
    private readonly IDateTime _dateTime;
    private readonly IFileStorageService _fileStorage;

    /// <summary>
    /// Required document types for a valid bid submission.
    /// </summary>
    private static readonly BidDocumentType[] RequiredDocumentTypes = new[]
    {
        BidDocumentType.PricedBOQ,
        BidDocumentType.Methodology,
        BidDocumentType.TeamCVs,
        BidDocumentType.Program,
        BidDocumentType.HSEPlan
    };

    public SubmitBidCommandHandler(
        IApplicationDbContext context,
        IMediator mediator,
        IEmailService emailService,
        IDateTime dateTime,
        IFileStorageService fileStorage)
    {
        _context = context;
        _mediator = mediator;
        _emailService = emailService;
        _dateTime = dateTime;
        _fileStorage = fileStorage;
    }

    public async Task<SubmitBidResultDto> Handle(
        SubmitBidCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists
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

        // Verify bidder exists
        var bidder = await _context.Bidders
            .FirstOrDefaultAsync(b => b.Id == request.BidderId, cancellationToken);

        if (bidder == null)
        {
            throw new NotFoundException("Bidder", request.BidderId);
        }

        // Verify bidder is invited
        var isInvited = await _context.TenderBidders
            .AnyAsync(tb =>
                tb.TenderId == request.TenderId &&
                tb.BidderId == request.BidderId,
                cancellationToken);

        if (!isInvited)
        {
            throw new InvalidOperationException("Bidder is not invited to this tender.");
        }

        // Get the pending bid submission
        var bidSubmission = await _context.BidSubmissions
            .Include(b => b.BidDocuments)
            .FirstOrDefaultAsync(b =>
                b.TenderId == request.TenderId &&
                b.BidderId == request.BidderId &&
                b.ReceiptNumber == string.Empty, // Pending submission
                cancellationToken);

        if (bidSubmission == null)
        {
            throw new InvalidOperationException("No pending bid submission found. Please upload the required files first.");
        }

        // Check if bid has already been submitted (has receipt number)
        var existingSubmission = await _context.BidSubmissions
            .AnyAsync(b =>
                b.TenderId == request.TenderId &&
                b.BidderId == request.BidderId &&
                b.ReceiptNumber != string.Empty,
                cancellationToken);

        if (existingSubmission)
        {
            throw new InvalidOperationException("A bid has already been submitted for this tender.");
        }

        // Validate all required documents are uploaded
        var uploadedDocTypes = bidSubmission.BidDocuments
            .Select(d => d.DocumentType)
            .ToHashSet();

        var missingDocTypes = RequiredDocumentTypes
            .Where(dt => !uploadedDocTypes.Contains(dt))
            .ToList();

        if (missingDocTypes.Any())
        {
            var missingNames = string.Join(", ", missingDocTypes.Select(d => d.ToString()));
            throw new InvalidOperationException($"Missing required documents: {missingNames}");
        }

        // Check if submission is late
        var now = _dateTime.UtcNow;
        var isLate = now > tender.SubmissionDeadline;

        // Generate receipt number: REC-{tenderId-short}-{sequence}
        var tenderIdShort = tender.Id.ToString("N").Substring(0, 8).ToUpper();
        var existingCount = await _context.BidSubmissions
            .CountAsync(b => b.TenderId == request.TenderId && b.ReceiptNumber != string.Empty, cancellationToken);
        var sequence = (existingCount + 1).ToString("D4");
        var receiptNumber = $"REC-{tenderIdShort}-{sequence}";

        // Update bid submission
        bidSubmission.SubmissionTime = now;
        bidSubmission.IsLate = isLate;
        bidSubmission.BidValidityDays = request.BidValidityDays;
        bidSubmission.ReceiptNumber = receiptNumber;
        bidSubmission.Status = BidSubmissionStatus.Submitted;
        bidSubmission.UpdatedAt = now;

        await _context.SaveChangesAsync(cancellationToken);

        // Build receipt DTO
        var receipt = new BidReceiptDto
        {
            ReceiptNumber = receiptNumber,
            BidId = bidSubmission.Id,
            TenderId = tender.Id,
            TenderTitle = tender.Title,
            TenderReference = tender.Reference,
            SubmittedAt = now,
            Timezone = "UTC",
            BidderCompanyName = bidder.CompanyName,
            IsLate = isLate,
            Files = bidSubmission.BidDocuments.Select(d => new BidReceiptFileDto
            {
                DocumentType = d.DocumentType.ToString(),
                FileName = d.FileName,
                FileSizeBytes = d.FileSizeBytes,
                FileSizeFormatted = FormatFileSize(d.FileSizeBytes)
            }).ToList()
        };

        // Generate receipt PDF
        var pdfCommand = new GenerateBidReceiptPdfCommand
        {
            BidSubmissionId = bidSubmission.Id
        };

        var pdfResult = await _mediator.Send(pdfCommand, cancellationToken);

        // Store PDF path in bid submission
        bidSubmission.ReceiptPdfPath = pdfResult.FilePath;
        await _context.SaveChangesAsync(cancellationToken);

        // Send receipt email to bidder
        await SendReceiptEmailAsync(bidder, tender, receipt, pdfResult.PdfContent, cancellationToken);

        var message = isLate
            ? "Bid submitted successfully. Note: This submission is marked as LATE as it was received after the deadline."
            : "Bid submitted successfully.";

        return new SubmitBidResultDto
        {
            BidId = bidSubmission.Id,
            Receipt = receipt,
            IsLate = isLate,
            Message = message
        };
    }

    /// <summary>
    /// Sends the bid receipt email to the bidder.
    /// </summary>
    private async Task SendReceiptEmailAsync(
        Domain.Entities.Bidder bidder,
        Domain.Entities.Tender tender,
        BidReceiptDto receipt,
        byte[] pdfContent,
        CancellationToken cancellationToken)
    {
        var filesHtml = string.Join("", receipt.Files.Select(f =>
            $"<tr><td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;\">{f.DocumentType}</td>" +
            $"<td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb;\">{f.FileName}</td>" +
            $"<td style=\"padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;\">{f.FileSizeFormatted}</td></tr>"));

        var mergeFields = new Dictionary<string, string>
        {
            { "BidderName", bidder.ContactPerson },
            { "CompanyName", bidder.CompanyName },
            { "TenderTitle", tender.Title },
            { "TenderReference", tender.Reference },
            { "SubmissionTime", receipt.SubmittedAt.ToString("yyyy-MM-dd HH:mm:ss 'UTC'") },
            { "ReceiptNumber", receipt.ReceiptNumber },
            { "FilesTable", filesHtml },
            { "IsLate", receipt.IsLate ? "YES - LATE SUBMISSION" : "On Time" }
        };

        var attachment = new EmailAttachment
        {
            FileName = $"BidReceipt-{receipt.ReceiptNumber}.pdf",
            Content = pdfContent,
            ContentType = "application/pdf"
        };

        await _emailService.SendTemplatedEmailAsync(
            bidder.Email,
            "BidReceiptTemplate",
            mergeFields,
            cancellationToken);
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
