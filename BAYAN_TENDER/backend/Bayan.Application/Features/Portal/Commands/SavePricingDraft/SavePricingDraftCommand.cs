using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Commands.SavePricingDraft;

/// <summary>
/// Command to save (or update) the bidder's pricing draft.
/// Creates a BidSubmission with Draft status if none exists,
/// then upserts BidPricing rows for each entry.
/// </summary>
public class SavePricingDraftCommand : IRequest<SavePricingDraftResult>
{
    /// <summary>
    /// The tender to save pricing for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The bidder saving the draft.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// The pricing entries to save.
    /// </summary>
    public List<PricingEntryDto> Entries { get; set; } = new();
}

/// <summary>
/// Result of saving a pricing draft.
/// </summary>
public class SavePricingDraftResult
{
    /// <summary>
    /// The BidSubmission ID for the draft.
    /// </summary>
    public Guid DraftId { get; set; }

    /// <summary>
    /// When the draft was saved.
    /// </summary>
    public DateTime SavedAt { get; set; }

    /// <summary>
    /// Updated grand total.
    /// </summary>
    public decimal GrandTotal { get; set; }

    /// <summary>
    /// Updated completion percentage.
    /// </summary>
    public int CompletionPercentage { get; set; }
}
