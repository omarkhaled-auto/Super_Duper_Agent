using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Boq.Services;

/// <summary>
/// Service for calculating roll-up totals in a hierarchical BOQ.
/// Handles sub-items -> items -> bills -> grand total aggregation
/// based on the tender's pricing level.
/// </summary>
public interface IBoqRollUpService
{
    /// <summary>
    /// Gets the IDs of all priceable nodes based on the tender's pricing level.
    /// - SubItem level: all non-group (leaf) items
    /// - Item level: all top-level items (no parent)
    /// - Bill level: all top-level sections (bills)
    /// </summary>
    Task<PriceableNodes> GetPriceableNodeIdsAsync(
        Guid tenderId, CancellationToken ct = default);

    /// <summary>
    /// Calculates the grand total for a bid submission by summing
    /// at the appropriate pricing level.
    /// </summary>
    Task<decimal> CalculateGrandTotalAsync(
        Guid tenderId, Guid bidSubmissionId, CancellationToken ct = default);

    /// <summary>
    /// Calculates totals per bill (top-level section).
    /// </summary>
    Task<List<BillTotal>> CalculateBillTotalsAsync(
        Guid tenderId, Guid bidSubmissionId, CancellationToken ct = default);

    /// <summary>
    /// Calculates totals per item (only meaningful at sub-item pricing level,
    /// where group items aggregate their children).
    /// </summary>
    Task<List<ItemTotal>> CalculateItemTotalsAsync(
        Guid tenderId, Guid bidSubmissionId, CancellationToken ct = default);
}

/// <summary>
/// Identifies priceable nodes and the pricing level in use.
/// </summary>
public class PriceableNodes
{
    /// <summary>
    /// The pricing level for this tender.
    /// </summary>
    public PricingLevel PricingLevel { get; set; }

    /// <summary>
    /// IDs of items that are priceable (for Item/SubItem levels).
    /// </summary>
    public List<Guid> ItemIds { get; set; } = new();

    /// <summary>
    /// IDs of sections that are priceable (for Bill level).
    /// </summary>
    public List<Guid> SectionIds { get; set; } = new();

    /// <summary>
    /// Total count of priceable nodes.
    /// </summary>
    public int Count => ItemIds.Count + SectionIds.Count;
}

/// <summary>
/// Total amount for a bill (top-level section).
/// </summary>
public class BillTotal
{
    public Guid SectionId { get; set; }
    public string SectionNumber { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public decimal Total { get; set; }
}

/// <summary>
/// Total amount for an item (group or standalone).
/// </summary>
public class ItemTotal
{
    public Guid ItemId { get; set; }
    public string ItemNumber { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public Guid SectionId { get; set; }
    public decimal Total { get; set; }
    public bool IsGroup { get; set; }
}
