using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;

namespace Bayan.Application.Features.BidAnalysis.Commands.MatchBidItems;

/// <summary>
/// Command to match bid items with BOQ items using exact and fuzzy matching.
/// </summary>
public class MatchBidItemsCommand : IRequest<MatchResultDto>
{
    /// <summary>
    /// Tender ID the bid belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bid submission ID.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// Bid items to match (from mapping step).
    /// </summary>
    public List<ImportBidItemDto> Items { get; set; } = new();

    /// <summary>
    /// Minimum confidence threshold for fuzzy matching (default 80%).
    /// </summary>
    public double FuzzyMatchThreshold { get; set; } = 80.0;

    /// <summary>
    /// Number of alternative matches to return for unmatched items.
    /// </summary>
    public int AlternativeMatchCount { get; set; } = 3;

    public MatchBidItemsCommand()
    {
    }

    public MatchBidItemsCommand(Guid tenderId, Guid bidId, List<ImportBidItemDto> items)
    {
        TenderId = tenderId;
        BidId = bidId;
        Items = items;
    }
}
