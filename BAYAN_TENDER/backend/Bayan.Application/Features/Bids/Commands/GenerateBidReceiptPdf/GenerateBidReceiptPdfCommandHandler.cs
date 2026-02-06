using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.GenerateBidReceiptPdf;

/// <summary>
/// Handler for the GenerateBidReceiptPdfCommand.
/// </summary>
public class GenerateBidReceiptPdfCommandHandler : IRequestHandler<GenerateBidReceiptPdfCommand, GenerateBidReceiptPdfResult>
{
    private readonly IApplicationDbContext _context;
    private readonly IPdfService _pdfService;
    private readonly IFileStorageService _fileStorage;

    public GenerateBidReceiptPdfCommandHandler(
        IApplicationDbContext context,
        IPdfService pdfService,
        IFileStorageService fileStorage)
    {
        _context = context;
        _pdfService = pdfService;
        _fileStorage = fileStorage;
    }

    public async Task<GenerateBidReceiptPdfResult> Handle(
        GenerateBidReceiptPdfCommand request,
        CancellationToken cancellationToken)
    {
        // Load bid submission with related entities
        var bidSubmission = await _context.BidSubmissions
            .Include(b => b.Tender)
            .Include(b => b.Bidder)
            .Include(b => b.BidDocuments)
            .FirstOrDefaultAsync(b => b.Id == request.BidSubmissionId, cancellationToken);

        if (bidSubmission == null)
        {
            throw new NotFoundException("BidSubmission", request.BidSubmissionId);
        }

        // Generate the PDF
        var pdfContent = await _pdfService.GenerateBidReceiptPdfAsync(
            bidSubmission,
            bidSubmission.Tender,
            bidSubmission.Bidder,
            bidSubmission.BidDocuments,
            cancellationToken);

        // Store the PDF in MinIO
        var fileName = $"Receipt-{bidSubmission.ReceiptNumber}.pdf";
        var storagePath = $"bid-receipts/{bidSubmission.TenderId}/{bidSubmission.BidderId}";

        using var stream = new MemoryStream(pdfContent);
        var filePath = await _fileStorage.UploadFileAsync(
            stream,
            fileName,
            "application/pdf",
            storagePath,
            cancellationToken);

        return new GenerateBidReceiptPdfResult
        {
            PdfContent = pdfContent,
            FilePath = filePath
        };
    }
}
