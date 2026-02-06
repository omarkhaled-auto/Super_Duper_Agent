namespace Bayan.Application.Features.Bids.DTOs;

/// <summary>
/// Data transfer object for late bid decision result.
/// </summary>
public class LateBidDecisionDto
{
    /// <summary>
    /// ID of the bid submission.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// Whether the late bid was accepted.
    /// </summary>
    public bool Accepted { get; set; }

    /// <summary>
    /// Reason for rejection (if not accepted).
    /// </summary>
    public string? Reason { get; set; }

    /// <summary>
    /// User who made the decision.
    /// </summary>
    public Guid DecisionBy { get; set; }

    /// <summary>
    /// Name of user who made the decision.
    /// </summary>
    public string DecisionByName { get; set; } = string.Empty;

    /// <summary>
    /// Timestamp of the decision.
    /// </summary>
    public DateTime DecisionAt { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderName { get; set; } = string.Empty;

    /// <summary>
    /// Bidder email address (for notification).
    /// </summary>
    public string BidderEmail { get; set; } = string.Empty;

    /// <summary>
    /// Whether notification was sent to the bidder.
    /// </summary>
    public bool NotificationSent { get; set; }
}
