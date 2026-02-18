using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Tenders.Commands.SetPricingLevel;

/// <summary>
/// Command for setting the pricing level on a tender.
/// Cannot be changed after bids have been submitted.
/// </summary>
public class SetPricingLevelCommand : IRequest<SetPricingLevelResult?>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The pricing level to set (Bill, Item, SubItem).
    /// </summary>
    public PricingLevel PricingLevel { get; set; }
}

/// <summary>
/// Result of setting the pricing level.
/// </summary>
public class SetPricingLevelResult
{
    /// <summary>
    /// The tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The new pricing level.
    /// </summary>
    public PricingLevel PricingLevel { get; set; }

    /// <summary>
    /// Number of priceable nodes at this level.
    /// </summary>
    public int PriceableNodeCount { get; set; }
}
