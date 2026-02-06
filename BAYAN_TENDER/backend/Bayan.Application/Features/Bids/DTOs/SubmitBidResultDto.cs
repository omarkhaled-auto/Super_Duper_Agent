namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Result of submitting a bid.
/// </summary>
public class SubmitBidResultDto
{
    /// <summary>
    /// ID of the created bid submission.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// Receipt information.
    /// </summary>
    public BidReceiptDto Receipt { get; set; } = null!;

    /// <summary>
    /// Whether the submission was late.
    /// </summary>
    public bool IsLate { get; set; }

    /// <summary>
    /// Message to display to the user.
    /// </summary>
    public string Message { get; set; } = string.Empty;
}
