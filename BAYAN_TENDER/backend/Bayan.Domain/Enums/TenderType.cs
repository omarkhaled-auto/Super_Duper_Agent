namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the types of tender procedures.
/// </summary>
public enum TenderType
{
    /// <summary>
    /// Open tender accessible to all qualified bidders.
    /// </summary>
    Open = 0,

    /// <summary>
    /// Selective tender with pre-qualified bidders.
    /// </summary>
    Selective = 1,

    /// <summary>
    /// Negotiated tender with specific suppliers.
    /// </summary>
    Negotiated = 2
}
