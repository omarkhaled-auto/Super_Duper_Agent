namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Data transfer object for submitting a bid.
/// </summary>
public class SubmitBidDto
{
    /// <summary>
    /// ID of the tender to submit the bid for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bid validity period in days.
    /// </summary>
    public int BidValidityDays { get; set; } = 90;

    /// <summary>
    /// List of uploaded file IDs to include in the submission.
    /// </summary>
    public List<Guid> FileIds { get; set; } = new();
}
