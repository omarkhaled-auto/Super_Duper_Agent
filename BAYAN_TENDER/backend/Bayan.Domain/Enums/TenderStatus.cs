namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the possible statuses of a tender.
/// </summary>
public enum TenderStatus
{
    /// <summary>
    /// Tender is being prepared and not yet published.
    /// </summary>
    Draft = 0,

    /// <summary>
    /// Tender is open for bidding.
    /// </summary>
    Active = 1,

    /// <summary>
    /// Tender is closed for bidding and under evaluation.
    /// </summary>
    Evaluation = 2,

    /// <summary>
    /// Tender has been awarded to a bidder.
    /// </summary>
    Awarded = 3,

    /// <summary>
    /// Tender has been cancelled.
    /// </summary>
    Cancelled = 4
}
