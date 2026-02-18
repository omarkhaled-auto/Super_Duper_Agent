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
            // Get tender to check pricing level
            var tender = await _context.Tenders
                .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

            if (tender == null)
            {
                throw new NotFoundException("Tender", request.TenderId);
            }

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
            _logger.LogInformation("Starting exact match for {Count} bid items", request.Items.Count);

            foreach (var bidItem in request.Items)
            {
                if (string.IsNullOrWhiteSpace(bidItem.ItemNumber))
                {
                    _logger.LogDebug("Row {Row}: Skipping - no item number", bidItem.RowIndex);
                    continue;
                }

                var normalizedBidItemNumber = NormalizeItemNumber(bidItem.ItemNumber);
                _logger.LogDebug("Row {Row}: Bidder item '{Bid}' normalized to '{Norm}'",
                    bidItem.RowIndex, bidItem.ItemNumber, normalizedBidItemNumber);

                var exactMatch = boqItems.FirstOrDefault(b =>
                    NormalizeItemNumber(b.ItemNumber).Equals(normalizedBidItemNumber, StringComparison.OrdinalIgnoreCase));

                if (exactMatch != null && !matchedBoqIds.Contains(exactMatch.Id))
                {
                    _logger.LogInformation("Row {Row}: EXACT MATCH '{Bid}' → BOQ '{Boq}'",
                        bidItem.RowIndex, bidItem.ItemNumber, exactMatch.ItemNumber);
                    result.ExactMatches.Add(CreateMatchDto(bidItem, exactMatch, MatchType.ExactMatch, 100));
                    matchedBoqIds.Add(exactMatch.Id);
                }
                else if (exactMatch == null)
                {
                    _logger.LogDebug("Row {Row}: No exact match for '{Bid}' (normalized: '{Norm}')",
                        bidItem.RowIndex, bidItem.ItemNumber, normalizedBidItemNumber);
                }
            }

            _logger.LogInformation("Exact matching complete: {Count} exact matches found", result.ExactMatches.Count);

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

            // Persist BidPricing records for matched and extra items
            // Clear any existing pricing from previous attempts
            var existingPricing = await _context.BidPricings
                .Where(bp => bp.BidSubmissionId == bid.Id)
                .ToListAsync(cancellationToken);
            if (existingPricing.Count > 0)
            {
                _context.BidPricings.RemoveRange(existingPricing);
            }

            // Create BidPricing for exact matches
            foreach (var match in result.ExactMatches)
            {
                _context.BidPricings.Add(CreateBidPricing(bid.Id, match, MatchType.ExactMatch, tender.PricingLevel));
            }
            // Create BidPricing for fuzzy matches
            foreach (var match in result.FuzzyMatches)
            {
                _context.BidPricings.Add(CreateBidPricing(bid.Id, match, MatchType.FuzzyMatch, tender.PricingLevel));
            }
            // Create BidPricing for extra/unmatched items
            foreach (var match in result.Unmatched)
            {
                _context.BidPricings.Add(CreateBidPricing(bid.Id, match, MatchType.ExtraItem, tender.PricingLevel));
            }
            // Create NoBid BidPricing for BOQ items not covered
            foreach (var noBid in result.NoBidItems)
            {
                _context.BidPricings.Add(new BidPricing
                {
                    Id = Guid.NewGuid(),
                    BidSubmissionId = bid.Id,
                    BoqItemId = noBid.BoqItemId,
                    BidderItemNumber = noBid.ItemNumber,
                    BidderDescription = noBid.Description,
                    BidderQuantity = noBid.Quantity,
                    BidderUom = noBid.Uom,
                    NativeCurrency = "AED",
                    MatchType = MatchType.NoBid,
                    MatchConfidence = 0,
                    IsNoBid = true,
                    IsIncludedInTotal = false
                });
            }

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

    private static BidPricing CreateBidPricing(
        Guid bidSubmissionId,
        BidItemMatchDto match,
        MatchType matchType,
        PricingLevel pricingLevel)
    {
        // Determine if this item should be included in total based on pricing level
        // This prevents double-counting when hierarchy has multiple levels priced
        bool shouldIncludeInTotal = matchType != MatchType.ExtraItem;

        if (shouldIncludeInTotal)
        {
            switch (pricingLevel)
            {
                case PricingLevel.SubItem:
                    // SubItem level: Only include leaf items with actual unit rates
                    // Excludes item groups (which show subtotals but no rates)
                    // Example: Include "1.01.a" (has rate), exclude "1.01" (subtotal)
                    shouldIncludeInTotal = match.BidUnitRate.HasValue && match.BidUnitRate.Value > 0;
                    break;

                case PricingLevel.Item:
                    // Item level: Only include items/groups (not sub-items)
                    // Contractor prices at group level like "1.01 Mobilization = 346k"
                    // Example: Include "1.01" (priced), exclude "1.01.a" (child detail)
                    var itemNumber = match.BidItemNumber ?? string.Empty;
                    var hasSubItemSuffix = itemNumber.Contains('.') &&
                        itemNumber.Split('.').Length > 2 &&
                        itemNumber.Split('.').Last().Length == 1; // Ends with single letter like ".a"
                    shouldIncludeInTotal = !hasSubItemSuffix;
                    break;

                case PricingLevel.Bill:
                    // Bill level: Only include bill-level items
                    // Contractor prices entire bills like "Bill 1 = 695k"
                    // Example: Include bills (no dots in item number), exclude items/sub-items
                    shouldIncludeInTotal = !match.BidItemNumber?.Contains('.') ?? false;
                    break;

                default:
                    // Unknown pricing level - include all to be safe
                    shouldIncludeInTotal = true;
                    break;
            }
        }

        return new BidPricing
        {
            Id = Guid.NewGuid(),
            BidSubmissionId = bidSubmissionId,
            BoqItemId = match.MatchedBoqItemId,
            BidderItemNumber = match.BidItemNumber,
            BidderDescription = match.BidDescription,
            BidderQuantity = match.BidQuantity,
            BidderUom = match.BidUom,
            NativeUnitRate = match.BidUnitRate,
            NativeAmount = match.BidAmount,
            NativeCurrency = match.Currency ?? "AED",
            MatchType = matchType,
            MatchConfidence = match.Confidence,
            IsIncludedInTotal = shouldIncludeInTotal
        };
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
