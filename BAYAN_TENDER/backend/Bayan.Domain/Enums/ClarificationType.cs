namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the type of clarification.
/// </summary>
public enum ClarificationType
{
    /// <summary>
    /// Question submitted by a bidder.
    /// </summary>
    BidderQuestion = 0,

    /// <summary>
    /// Internal request for information.
    /// </summary>
    InternalRFI = 1,

    /// <summary>
    /// Request for information from client.
    /// </summary>
    ClientRFI = 2
}
