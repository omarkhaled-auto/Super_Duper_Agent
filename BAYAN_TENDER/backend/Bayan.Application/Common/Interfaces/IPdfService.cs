using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for PDF generation services.
/// </summary>
public interface IPdfService
{
    /// <summary>
    /// Generates a PDF document for a clarification bulletin.
    /// </summary>
    /// <param name="bulletin">The clarification bulletin entity.</param>
    /// <param name="tender">The associated tender entity.</param>
    /// <param name="clarifications">The clarifications to include in the bulletin.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The generated PDF as a byte array.</returns>
    Task<byte[]> GenerateBulletinPdfAsync(
        ClarificationBulletin bulletin,
        Tender tender,
        IEnumerable<Clarification> clarifications,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Generates a PDF receipt for a bid submission.
    /// </summary>
    /// <param name="bidSubmission">The bid submission entity.</param>
    /// <param name="tender">The associated tender entity.</param>
    /// <param name="bidder">The bidder who submitted.</param>
    /// <param name="bidDocuments">The documents included in the submission.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The generated PDF as a byte array.</returns>
    Task<byte[]> GenerateBidReceiptPdfAsync(
        BidSubmission bidSubmission,
        Tender tender,
        Bidder bidder,
        IEnumerable<BidDocument> bidDocuments,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Generates an award pack PDF document.
    /// </summary>
    /// <param name="data">The award pack data containing all evaluation results.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The generated PDF as a byte array.</returns>
    Task<byte[]> GenerateAwardPackPdfAsync(
        AwardPackDataDto data,
        CancellationToken cancellationToken = default);
}
