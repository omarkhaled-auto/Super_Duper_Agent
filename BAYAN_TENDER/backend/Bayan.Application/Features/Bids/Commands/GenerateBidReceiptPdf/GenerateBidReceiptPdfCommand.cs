using MediatR;

namespace Bayan.Application.Features.Bids.Commands.GenerateBidReceiptPdf;

/// <summary>
/// Command to generate a PDF receipt for a bid submission.
/// </summary>
public class GenerateBidReceiptPdfCommand : IRequest<GenerateBidReceiptPdfResult>
{
    /// <summary>
    /// ID of the bid submission to generate the receipt for.
    /// </summary>
    public Guid BidSubmissionId { get; set; }
}

/// <summary>
/// Result of generating a bid receipt PDF.
/// </summary>
public class GenerateBidReceiptPdfResult
{
    /// <summary>
    /// The generated PDF content.
    /// </summary>
    public byte[] PdfContent { get; set; } = Array.Empty<byte>();

    /// <summary>
    /// Path where the PDF was stored in MinIO.
    /// </summary>
    public string FilePath { get; set; } = string.Empty;
}
