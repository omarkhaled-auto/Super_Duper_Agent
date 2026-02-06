namespace Bayan.Application.Features.Addenda.DTOs;

/// <summary>
/// Data transfer object for addendum acknowledgment.
/// </summary>
public class AddendumAcknowledgmentDto
{
    /// <summary>
    /// Unique identifier of the acknowledgment.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// ID of the addendum being acknowledged.
    /// </summary>
    public Guid AddendumId { get; set; }

    /// <summary>
    /// ID of the bidder acknowledging.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Name of the bidder company.
    /// </summary>
    public string BidderName { get; set; } = string.Empty;

    /// <summary>
    /// Contact person of the bidder.
    /// </summary>
    public string BidderContactPerson { get; set; } = string.Empty;

    /// <summary>
    /// Email address of the bidder.
    /// </summary>
    public string BidderEmail { get; set; } = string.Empty;

    /// <summary>
    /// When the email notification was sent.
    /// </summary>
    public DateTime? EmailSentAt { get; set; }

    /// <summary>
    /// When the email was opened/viewed.
    /// </summary>
    public DateTime? EmailOpenedAt { get; set; }

    /// <summary>
    /// When the bidder acknowledged the addendum.
    /// </summary>
    public DateTime? AcknowledgedAt { get; set; }

    /// <summary>
    /// Whether the bidder has acknowledged this addendum.
    /// </summary>
    public bool IsAcknowledged => AcknowledgedAt.HasValue;
}
