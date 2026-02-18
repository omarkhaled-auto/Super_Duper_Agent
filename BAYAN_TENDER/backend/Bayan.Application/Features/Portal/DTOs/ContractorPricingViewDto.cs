using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Portal.DTOs;

/// <summary>
/// Top-level DTO returned by the contractor pricing view endpoint.
/// Contains the BOQ tree filtered by pricing level plus any draft data.
/// </summary>
public class ContractorPricingViewDto
{
    /// <summary>
    /// The tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The pricing level configured for this tender (Bill, Item, SubItem).
    /// </summary>
    public PricingLevel PricingLevel { get; set; }

    /// <summary>
    /// Hierarchical tree of pricing nodes the bidder can price.
    /// </summary>
    public List<PricingNodeDto> Nodes { get; set; } = new();

    /// <summary>
    /// The bidder's current draft data (null if no draft exists).
    /// </summary>
    public PricingDraftDto? Draft { get; set; }
}

/// <summary>
/// A single node in the pricing tree. Can represent a bill (section),
/// an item, or a sub-item depending on the tender's pricing level.
/// </summary>
public class PricingNodeDto
{
    /// <summary>
    /// The entity ID (BoqSection.Id or BoqItem.Id).
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// The type of node: "bill", "item", or "sub_item".
    /// </summary>
    public string NodeType { get; set; } = string.Empty;

    /// <summary>
    /// Display number (section number or item number).
    /// </summary>
    public string Number { get; set; } = string.Empty;

    /// <summary>
    /// Description or title of the node.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Quantity (null for bills and group items).
    /// </summary>
    public decimal? Quantity { get; set; }

    /// <summary>
    /// Unit of measurement (null for bills and group items).
    /// </summary>
    public string? Uom { get; set; }

    /// <summary>
    /// Whether this node accepts pricing input from the bidder.
    /// </summary>
    public bool IsPriceable { get; set; }

    /// <summary>
    /// Whether this node is read-only context (shown but not editable).
    /// </summary>
    public bool IsReadOnly { get; set; }

    /// <summary>
    /// Child nodes in the hierarchy.
    /// </summary>
    public List<PricingNodeDto> Children { get; set; } = new();
}

/// <summary>
/// Represents the bidder's draft pricing state.
/// </summary>
public class PricingDraftDto
{
    /// <summary>
    /// The BidSubmission ID for the draft (null if no draft exists yet).
    /// </summary>
    public Guid? DraftId { get; set; }

    /// <summary>
    /// When the draft was last saved.
    /// </summary>
    public DateTime? LastSavedAt { get; set; }

    /// <summary>
    /// The pricing entries the bidder has saved so far.
    /// </summary>
    public List<PricingEntryDto> Entries { get; set; } = new();

    /// <summary>
    /// The calculated grand total from all entries.
    /// </summary>
    public decimal GrandTotal { get; set; }

    /// <summary>
    /// Percentage of priceable nodes that have been priced (0-100).
    /// </summary>
    public int CompletionPercentage { get; set; }
}

/// <summary>
/// A single pricing entry from the bidder.
/// </summary>
public class PricingEntryDto
{
    /// <summary>
    /// The node ID this entry prices (BoqItem.Id or BoqSection.Id).
    /// </summary>
    public Guid NodeId { get; set; }

    /// <summary>
    /// Unit rate entered by the bidder (for item/sub-item level pricing).
    /// </summary>
    public decimal? UnitRate { get; set; }

    /// <summary>
    /// Lump sum entered by the bidder (for bill level pricing).
    /// </summary>
    public decimal? LumpSum { get; set; }

    /// <summary>
    /// Calculated amount (UnitRate * Quantity or LumpSum).
    /// </summary>
    public decimal? Amount { get; set; }
}
