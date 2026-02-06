using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a bidder's acknowledgment of an addendum.
/// </summary>
public class AddendumAcknowledgment : BaseEntity
{
    /// <summary>
    /// Addendum being acknowledged.
    /// </summary>
    public Guid AddendumId { get; set; }

    /// <summary>
    /// Bidder acknowledging the addendum.
    /// </summary>
    public Guid BidderId { get; set; }

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

    // Navigation properties
    /// <summary>
    /// The addendum being acknowledged.
    /// </summary>
    public virtual Addendum Addendum { get; set; } = null!;

    /// <summary>
    /// The bidder acknowledging.
    /// </summary>
    public virtual Bidder Bidder { get; set; } = null!;
}
