using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Commands.SubmitPricing;

/// <summary>
/// Command to finalize and submit the bidder's in-app pricing.
/// Validates that all priceable nodes have been priced, then
/// transitions the BidSubmission from Draft to Submitted.
/// </summary>
public class SubmitPricingCommand : IRequest<SubmitPricingResult>
{
    /// <summary>
    /// The tender to submit pricing for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The bidder submitting the pricing.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// The final pricing entries to save before submitting.
    /// </summary>
    public List<PricingEntryDto> Entries { get; set; } = new();
}

/// <summary>
/// Result of a successful pricing submission.
/// </summary>
public class SubmitPricingResult
{
    /// <summary>
    /// The BidSubmission ID.
    /// </summary>
    public Guid SubmissionId { get; set; }

    /// <summary>
    /// The calculated grand total.
    /// </summary>
    public decimal GrandTotal { get; set; }

    /// <summary>
    /// When the bid was submitted.
    /// </summary>
    public DateTime SubmittedAt { get; set; }

    /// <summary>
    /// Receipt number for the submission.
    /// </summary>
    public string ReceiptNumber { get; set; } = string.Empty;
}
