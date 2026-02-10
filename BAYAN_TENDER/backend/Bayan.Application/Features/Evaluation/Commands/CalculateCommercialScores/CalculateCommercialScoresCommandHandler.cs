using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Commands.CalculateCommercialScores;

/// <summary>
/// Handler for CalculateCommercialScoresCommand.
/// Calculates commercial scores using formula: (Lowest Total / This Total) x 100
/// </summary>
public class CalculateCommercialScoresCommandHandler : IRequestHandler<CalculateCommercialScoresCommand, CalculateCommercialScoresResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<CalculateCommercialScoresCommandHandler> _logger;

    public CalculateCommercialScoresCommandHandler(
        IApplicationDbContext context,
        ILogger<CalculateCommercialScoresCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<CalculateCommercialScoresResultDto> Handle(
        CalculateCommercialScoresCommand request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Calculating commercial scores for tender {TenderId} " +
            "(IncludeProvisionalSums: {IncludePS}, IncludeAlternates: {IncludeAlt})",
            request.TenderId, request.IncludeProvisionalSums, request.IncludeAlternates);

        // Verify tender exists
        var tenderExists = await _context.Tenders
            .AnyAsync(t => t.Id == request.TenderId, cancellationToken);

        if (!tenderExists)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Get excluded item types based on settings
        var excludedTypes = new List<BoqItemType>();
        if (!request.IncludeProvisionalSums)
        {
            excludedTypes.Add(BoqItemType.ProvisionalSum);
        }
        if (!request.IncludeAlternates)
        {
            excludedTypes.Add(BoqItemType.Alternate);
        }

        // Get all imported bid submissions with their bidders
        var bidSubmissions = await _context.BidSubmissions
            .Include(bs => bs.Bidder)
            .Where(bs => bs.TenderId == request.TenderId)
            .Where(bs => bs.ImportStatus == BidImportStatus.Imported)
            .Where(bs => bs.Status != BidSubmissionStatus.Disqualified)
            .ToListAsync(cancellationToken);

        if (!bidSubmissions.Any())
        {
            _logger.LogWarning("No imported bids found for tender {TenderId}", request.TenderId);
            return new CalculateCommercialScoresResultDto
            {
                Scores = new List<CommercialScoreResultDto>(),
                CalculatedAt = DateTime.UtcNow,
                IncludeProvisionalSums = request.IncludeProvisionalSums,
                IncludeAlternates = request.IncludeAlternates
            };
        }

        if (bidSubmissions.Count < 3)
        {
            _logger.LogWarning(
                "Tender {TenderId} has only {BidderCount} bidders (recommended minimum is 3 for competitive evaluation)",
                request.TenderId, bidSubmissions.Count);
        }

        // Calculate totals for each bidder
        var bidderTotals = new List<(Guid BidderId, string CompanyName, decimal Total)>();

        foreach (var submission in bidSubmissions)
        {
            decimal total;

            if (excludedTypes.Any())
            {
                // Get BOQ items to exclude
                var excludedItemIds = await _context.BoqItems
                    .Where(bi => bi.TenderId == request.TenderId)
                    .Where(bi => excludedTypes.Contains(bi.ItemType))
                    .Select(bi => bi.Id)
                    .ToListAsync(cancellationToken);

                // Calculate total excluding specific item types
                total = await _context.BidPricings
                    .Where(bp => bp.BidSubmissionId == submission.Id)
                    .Where(bp => bp.IsIncludedInTotal)
                    .Where(bp => bp.BoqItemId == null || !excludedItemIds.Contains(bp.BoqItemId.Value))
                    .SumAsync(bp => bp.NormalizedAmount ?? 0, cancellationToken);
            }
            else
            {
                // Use the pre-calculated total from bid submission
                total = submission.NormalizedTotalAmount ?? 0;
            }

            bidderTotals.Add((submission.BidderId, submission.Bidder.CompanyName, total));
        }

        // Find lowest bid
        var lowestBid = bidderTotals.Min(bt => bt.Total);

        if (lowestBid <= 0)
        {
            _logger.LogWarning(
                "Invalid lowest bid amount ({LowestBid}) for tender {TenderId}",
                lowestBid, request.TenderId);
            throw new InvalidOperationException("Cannot calculate commercial scores: lowest bid amount is zero or negative.");
        }

        // Calculate scores and create/update CommercialScore records
        var scores = new List<CommercialScoreResultDto>();

        // Remove existing commercial scores for this tender with same settings
        var existingScores = await _context.CommercialScores
            .Where(cs => cs.TenderId == request.TenderId)
            .Where(cs => cs.IncludeProvisionalSums == request.IncludeProvisionalSums)
            .Where(cs => cs.IncludeAlternates == request.IncludeAlternates)
            .ToListAsync(cancellationToken);

        _context.CommercialScores.RemoveRange(existingScores);

        foreach (var (bidderId, companyName, total) in bidderTotals)
        {
            var score = total > 0 ? (lowestBid / total) * 100 : 0;

            scores.Add(new CommercialScoreResultDto
            {
                BidderId = bidderId,
                CompanyName = companyName,
                NormalizedTotalPrice = total,
                CommercialScore = Math.Round(score, 2)
            });
        }

        // Sort by score (highest first) and assign ranks
        scores = scores.OrderByDescending(s => s.CommercialScore).ToList();
        for (int i = 0; i < scores.Count; i++)
        {
            scores[i].Rank = i + 1;
        }

        // Save new commercial scores
        foreach (var score in scores)
        {
            var commercialScore = new CommercialScore
            {
                TenderId = request.TenderId,
                BidderId = score.BidderId,
                NormalizedTotalPrice = score.NormalizedTotalPrice,
                CommercialScoreValue = score.CommercialScore,
                Rank = score.Rank,
                IncludeProvisionalSums = request.IncludeProvisionalSums,
                IncludeAlternates = request.IncludeAlternates,
                CalculatedAt = DateTime.UtcNow
            };

            _context.CommercialScores.Add(commercialScore);
        }

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Commercial scores calculated for tender {TenderId}: {Count} bidders, " +
            "lowest bid: {LowestBid:C}",
            request.TenderId, scores.Count, lowestBid);

        return new CalculateCommercialScoresResultDto
        {
            Scores = scores,
            LowestBidAmount = lowestBid,
            IncludeProvisionalSums = request.IncludeProvisionalSums,
            IncludeAlternates = request.IncludeAlternates,
            CalculatedAt = DateTime.UtcNow
        };
    }
}
