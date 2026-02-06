namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the NDA status for tender-bidder relationships.
/// </summary>
public enum NdaStatus
{
    /// <summary>
    /// NDA not yet signed.
    /// </summary>
    Pending = 0,

    /// <summary>
    /// NDA has been signed.
    /// </summary>
    Signed = 1,

    /// <summary>
    /// NDA has expired.
    /// </summary>
    Expired = 2
}
