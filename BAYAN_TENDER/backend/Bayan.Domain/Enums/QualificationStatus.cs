namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the qualification status for bidders.
/// </summary>
public enum QualificationStatus
{
    /// <summary>
    /// Qualification pending review.
    /// </summary>
    Pending = 0,

    /// <summary>
    /// Bidder is qualified.
    /// </summary>
    Qualified = 1,

    /// <summary>
    /// Bidder qualification rejected.
    /// </summary>
    Rejected = 2,

    /// <summary>
    /// Bidder removed from tender.
    /// </summary>
    Removed = 3
}
