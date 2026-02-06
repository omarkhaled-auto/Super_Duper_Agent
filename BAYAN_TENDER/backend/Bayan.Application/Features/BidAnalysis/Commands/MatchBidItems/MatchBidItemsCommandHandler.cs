using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.BidAnalysis.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using MatchType = Bayan.Domain.Enums.MatchType;

namespace Bayan.Application.Features.BidAnalysis.Commands.MatchBidItems;

/// <summary>
/// Handler for MatchBidItemsCommand.
/// </summary>
public class MatchBidItemsCommandHandler : IRequestHandler<MatchBidItemsCommand, MatchResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IFuzzyMatchingService _fuzzyMatching;
    private readonly ILogger<MatchBidItemsCommandHandler> _logger;

    public MatchBidItemsCommandHandler(
        IApplicationDbContext context,
        IFuzzyMatchingService fuzzyMatching,
        ILogger<MatchBidItemsCommandHandler> logger)
    {
        _context = context;
        _fuzzyMatching = fuzzyMatching;
        _logger = logger;
    }

    public async Task<MatchResultDto> Handle(MatchBidItemsCommand request, CancellationToken cancellationToken)
    {
        // Get bid submission
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == request.BidId && b.TenderId == request.TenderId, cancellationToken);

        if (bid == null)
        {
            throw new NotFoundException("BidSubmission", request.BidId);
        }

        if (bid.ImportStatus != BidImportStatus.Mapped)
        {
            throw new InvalidOperationException($"Bid must be in 'Mapped' status to match items. Current status: {bid.ImportStatus}");
        }

        // Update status to matching
        bid.ImportStatus = BidImportStatus.Matching;
        await _context.SaveChangesAsync(cancellationToken);

        try
        {
            // Get BOQ items for the tender
            var boqItems = await _context.BoqItems
                .Include(b => b.Section)
                .Where(b => b.TenderId == request.TenderId)
                .ToListAsync(cancellationToken);

            if (boqItems.Count == 0)
            {
                _logger.LogWarning("No BOQ items found for tender {TenderId}", request.TenderId);
            }

            var result = new MatchResultDto();
            var matchedBoqIds = new HashSet<Guid>();

            // Step 1: Exact match by item number
            foreach (var bidItem in request.Items)
            {
                if (string.IsNullOrWhiteSpace(bidItem.ItemNumber))
                {
                    continue;
                }

                var normalizedBidItemNumber = NormalizeItemNumber(bidItem.ItemNumber);
                var exactMatch = boqItems.FirstOrDefault(b =>
                    NormalizeItemNumber(b.ItemNumber).Equals(normalizedBidItemNumber, StringComparison.OrdinalIgnoreCase));

                if (exactMatch != null && !matchedBoqIds.Contains(exactMatch.Id))
                {
                    result.ExactMatches.Add(CreateMatchDto(bidItem, exactMatch, MatchType.ExactMatch, 100));
                    matchedBoqIds.Add(exactMatch.Id);
                }
            }

            // Get items not yet matched
            var unmatchedBidItems = request.Items
                .Where(bi => !result.ExactMatches.Any(em => em.RowIndex == bi.RowIndex))
                .ToList();

            var remainingBoqItems = boqItems.Where(b => !matchedBoqIds.Contains(b.Id)).ToList();

            // Step 2: Fuzzy match by description
            foreach (var bidItem in unmatchedBidItems)
            {
                if (string.IsNullOrWhiteSpace(bidItem.Description))
                {
                    continue;
                }

                var fuzzyMatches = _fuzzyMatching.FindMatches(
                    bidItem.Description,
                    remainingBoqItems,
                    b => b.Description,
                    request.FuzzyMatchThreshold);

                var topMatch = fuzzyMatches.FirstOrDefault();

                if (topMatch.Match != null && topMatch.Confidence >= request.FuzzyMatchThreshold)
                {
                    var matchDto = CreateMatchDto(bidItem, topMatch.Match, MatchType.FuzzyMatch, (decimal)topMatch.Confidence);

                    // Add alternative matches for review
                    var alternatives = fuzzyMatches
                        .Skip(1)
                        .Take(request.AlternativeMatchCount)
                        .Select(m => new PotentialMatchDto
                        {
                            BoqItemId = m.Match.Id,
                            ItemNumber = m.Match.ItemNumber,
                            Description = m.Match.Description,
                            Quantity = m.Match.Quantity,
                            Uom = m.Match.Uom,
                            Confidence = (decimal)m.Confidence
                        })
                        .ToList();

                    matchDto.AlternativeMatches = alternatives;
                    matchDto.NeedsReview = topMatch.Confidence < 90; // Flag for review if confidence < 90%
                    matchDto.ReviewReason = matchDto.NeedsReview ? "Confidence below 90%" : null;

                    result.FuzzyMatches.Add(matchDto);
                    matchedBoqIds.Add(topMatch.Match.Id);
                    remainingBoqItems.Remove(topMatch.Match);
                }
            }

            // Step 3: Flag remaining bid items as unmatched or extra
            var stillUnmatched = request.Items
                .Where(bi =>
                    !result.ExactMatches.Any(em => em.RowIndex == bi.RowIndex) &&
                    !result.FuzzyMatches.Any(fm => fm.RowIndex == bi.RowIndex))
                .ToList();

            foreach (var bidItem in stillUnmatched)
            {
                var matchDto = new BidItemMatchDto
                {
                    RowIndex = bidItem.RowIndex,
                    BidItemNumber = bidItem.ItemNumber,
                    BidDescription = bidItem.Description,
                    BidQuantity = bidItem.Quantity,
                    BidUom = bidItem.Uom,
                    BidUnitRate = bidItem.UnitRate,
                    BidAmount = bidItem.Amount,
                    Currency = bidItem.Currency,
                    MatchType = MatchType.ExtraItem, // Default to extra item
                    Confidence = 0,
                    NeedsReview = true,
                    ReviewReason = "No matching BOQ item found"
                };

                // Find potential matches for manual review
                if (!string.IsNullOrWhiteSpace(bidItem.Description) && remainingBoqItems.Count > 0)
                {
                    var potentialMatches = _fuzzyMatching.FindMatches(
                        bidItem.Description,
                        remainingBoqItems,
                        b => b.Description,
                        0); // Get all matches regardless of threshold

                    matchDto.AlternativeMatches = potentialMatches
                        .Take(request.AlternativeMatchCount)
                        .Select(m => new PotentialMatchDto
                        {
                            BoqItemId = m.Match.Id,
                            ItemNumber = m.Match.ItemNumber,
                            Description = m.Match.Description,
                            Quantity = m.Match.Quantity,
                            Uom = m.Match.Uom,
                            Confidence = (decimal)m.Confidence
                        })
                        .ToList();
                }

                result.Unmatched.Add(matchDto);
            }

            // Step 4: Identify BOQ items with no bid
            foreach (var boqItem in remainingBoqItems.Where(b => !matchedBoqIds.Contains(b.Id)))
            {
                result.NoBidItems.Add(new NoBidItemDto
                {
                    BoqItemId = boqItem.Id,
                    ItemNumber = boqItem.ItemNumber,
                    Description = boqItem.Description,
                    Quantity = boqItem.Quantity,
                    Uom = boqItem.Uom,
                    SectionName = boqItem.Section?.Title
                });
            }

            // Calculate summary statistics
            result.Summary = CalculateSummary(result, request.Items.Count, boqItems.Count);

            // Update status to matched
            bid.ImportStatus = BidImportStatus.Matched;
            await _context.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "Matching complete for bid {BidId}: {ExactCount} exact, {FuzzyCount} fuzzy, {UnmatchedCount} unmatched, {NoBidCount} no-bid",
                request.BidId, result.Summary.ExactMatchCount, result.Summary.FuzzyMatchCount,
                result.Summary.UnmatchedCount, result.Summary.NoBidCount);

            return result;
        }
        catch (Exception ex) when (ex is not NotFoundException && ex is not InvalidOperationException)
        {
            _logger.LogError(ex, "Error matching items for bid {BidId}", request.BidId);

            bid.ImportStatus = BidImportStatus.Failed;
            await _context.SaveChangesAsync(cancellationToken);

            throw new InvalidOperationException($"Error matching items: {ex.Message}", ex);
        }
    }

    private static string NormalizeItemNumber(string itemNumber)
    {
        if (string.IsNullOrWhiteSpace(itemNumber))
        {
            return string.Empty;
        }

        // Remove common prefixes and normalize separators
        return itemNumber
            .Trim()
            .Replace(" ", "")
            .Replace("-", ".")
            .Replace("_", ".")
            .TrimStart('0')
            .ToUpperInvariant();
    }

    private static BidItemMatchDto CreateMatchDto(ImportBidItemDto bidItem, BoqItem boqItem, Domain.Enums.MatchType matchType, decimal confidence)
    {
        return new BidItemMatchDto
        {
            RowIndex = bidItem.RowIndex,
            BidItemNumber = bidItem.ItemNumber,
            BidDescription = bidItem.Description,
            BidQuantity = bidItem.Quantity,
            BidUom = bidItem.Uom,
            BidUnitRate = bidItem.UnitRate,
            BidAmount = bidItem.Amount,
            Currency = bidItem.Currency,
            MatchedBoqItemId = boqItem.Id,
            MatchedBoqItemNumber = boqItem.ItemNumber,
            MatchedBoqDescription = boqItem.Description,
            MatchedBoqQuantity = boqItem.Quantity,
            MatchedBoqUom = boqItem.Uom,
            MatchType = matchType,
            Confidence = confidence,
            NeedsReview = false
        };
    }

    private static MatchSummaryDto CalculateSummary(MatchResultDto result, int totalBidItems, int totalBoqItems)
    {
        var exactCount = result.ExactMatches.Count;
        var fuzzyCount = result.FuzzyMatches.Count;
        var unmatchedCount = result.Unmatched.Count;
        var noBidCount = result.NoBidItems.Count;

        var averageFuzzyConfidence = fuzzyCount > 0
            ? result.FuzzyMatches.Average(m => m.Confidence)
            : 0;

        var requiresReviewCount =
            result.FuzzyMatches.Count(m => m.NeedsReview) +
            result.Unmatched.Count;

        var matchedCount = exactCount + fuzzyCount;
        var matchPercentage = totalBoqItems > 0
            ? (decimal)matchedCount / totalBoqItems * 100
            : 0;

        return new MatchSummaryDto
        {
            TotalBidItems = totalBidItems,
            TotalBoqItems = totalBoqItems,
            ExactMatchCount = exactCount,
            FuzzyMatchCount = fuzzyCount,
            UnmatchedCount = unmatchedCount,
            ExtraItemCount = result.Unmatched.Count(u => u.MatchType == MatchType.ExtraItem),
            NoBidCount = noBidCount,
            MatchPercentage = Math.Round(matchPercentage, 2),
            AverageFuzzyConfidence = Math.Round(averageFuzzyConfidence, 2),
            RequiresReviewCount = requiresReviewCount
        };
    }
}
