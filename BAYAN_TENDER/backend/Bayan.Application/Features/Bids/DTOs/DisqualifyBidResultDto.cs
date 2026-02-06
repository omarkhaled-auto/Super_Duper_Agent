namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Data transfer object for bid disqualification result.
/// </summary>
public class DisqualifyBidResultDto
{
    /// <summary>
    /// ID of the bid submission.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// Reason for disqualification.
    /// </summary>
    public string Reason { get; set; } = string.Empty;

    /// <summary>
    /// User who disqualified the bid.
    /// </summary>
    public Guid DisqualifiedBy { get; set; }

    /// <summary>
    /// Name of user who disqualified the bid.
    /// </summary>
    public string DisqualifiedByName { get; set; } = string.Empty;

    /// <summary>
    /// Timestamp of the disqualification.
    /// </summary>
    public DateTime DisqualifiedAt { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderName { get; set; } = string.Empty;
}
