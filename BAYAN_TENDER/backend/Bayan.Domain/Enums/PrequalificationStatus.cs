namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the prequalification status for bidders.
/// </summary>
public enum PrequalificationStatus
{
    /// <summary>
    /// Prequalification pending.
    /// </summary>
    Pending = 0,

    /// <summary>
    /// Bidder is prequalified.
    /// </summary>
    Qualified = 1,

    /// <summary>
    /// Bidder prequalification rejected.
    /// </summary>
    Rejected = 2
}
