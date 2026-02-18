namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the pricing level for a tender's BOQ.
/// Determines at which hierarchy level bidders must provide prices.
/// </summary>
public enum PricingLevel
{
    /// <summary>
    /// Bidders provide one lump sum per bill (top-level sections).
    /// </summary>
    Bill = 0,

    /// <summary>
    /// Bidders provide a rate/amount per numbered item.
    /// </summary>
    Item = 1,

    /// <summary>
    /// Bidders provide a rate per sub-item (most granular).
    /// </summary>
    SubItem = 2
}
