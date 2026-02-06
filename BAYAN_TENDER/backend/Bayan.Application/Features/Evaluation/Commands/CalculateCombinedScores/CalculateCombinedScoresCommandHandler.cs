using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Commands.CalculateCombinedScores;

/// <summary>
/// Handler for CalculateCombinedScoresCommand.
/// Calculates combined scores using formula: (TechWeight/100 * TechScore) + (CommWeight/100 * CommScore)
/// </summary>
public class CalculateCombinedScoresCommandHandler : IRequestHandler<CalculateCombinedScoresCommand, CombinedScorecardDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<CalculateCombinedScoresCommandHandler> _logger;

    public CalculateCombinedScoresCommandHandler(
        IApplicationDbContext context,
        ILogger<CalculateCombinedScoresCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<CombinedScorecardDto> Handle(
        CalculateCombinedScoresCommand request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Calculating combined scores for tender {TenderId} " +
            "(TechWeight: {TechWeight}, CommWeight: {CommWeight})",
            request.TenderId, request.TechnicalWeight, request.CommercialWeight);

        // Get tender with validation
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Use provided weights or fall back to tender defaults
        var techWeight = request.TechnicalWeight ?? tender.TechnicalWeight;
        var commWeight = request.CommercialWeight ?? tender.CommercialWeight;

        // Validate weights sum to 100
        if (techWeight + commWeight != 100)
        {
            throw new InvalidOperationException(
                $"Technical weight ({techWeight}) and commercial weight ({commWeight}) must sum to 100.");
        }

        // Get bidders with technical scores (average of submitted scores)
        var technicalScoresByBidder = await _context.TechnicalScores
            .Where(ts => ts.TenderId == request.TenderId)
            .Where(ts => !ts.IsDraft) // Only submitted scores
            .GroupBy(ts => ts.BidderId)
            .Select(g => new
            {
                BidderId = g.Key,
                AverageScore = g.Average(ts => ts.Score)
            })
            .ToDictionaryAsync(x => x.BidderId, x => x.AverageScore, cancellationToken);

        // Get commercial scores
        var commercialScores = await _context.CommercialScores
            .Include(cs => cs.Bidder)
            .Where(cs => cs.TenderId == request.TenderId)
            .OrderByDescending(cs => cs.CalculatedAt)
            .ToListAsync(cancellationToken);

        // Get unique bidders from commercial scores (latest calculation)
        var latestCommercialScores = commercialScores
            .GroupBy(cs => cs.BidderId)
            .Select(g => g.First())
            .ToDictionary(cs => cs.BidderId, cs => cs);

        if (!latestCommercialScores.Any())
        {
            _logger.LogWarning("No commercial scores found for tender {TenderId}", request.TenderId);
            return new CombinedScorecardDto
            {
                TenderId = request.TenderId,
                TenderReference = tender.Reference,
                TenderTitle = tender.Title,
                TechnicalWeight = techWeight,
                CommercialWeight = commWeight,
                Entries = new List<CombinedScoreEntryDto>(),
                CalculatedAt = DateTime.UtcNow
            };
        }

        // Calculate combined scores
        var combinedEntries = new List<(Guid BidderId, string CompanyName, decimal TechScore, decimal CommScore, decimal CombinedScore, decimal TotalPrice)>();

        foreach (var commercialScore in latestCommercialScores.Values)
        {
            // Get technical score average (default to 0 if not found)
            var techScore = technicalScoresByBidder.TryGetValue(commercialScore.BidderId, out var ts) ? ts : 0m;
            var commScore = commercialScore.CommercialScoreValue;

            // Calculate combined score: (TechWeight/100 * TechScore) + (CommWeight/100 * CommScore)
            var combinedScore = (techWeight / 100m * techScore) + (commWeight / 100m * commScore);

            combinedEntries.Add((
                commercialScore.BidderId,
                commercialScore.Bidder.CompanyName,
                techScore,
                commScore,
                Math.Round(combinedScore, 2),
                commercialScore.NormalizedTotalPrice
            ));
        }

        // Sort by combined score (highest first) and assign ranks
        combinedEntries = combinedEntries.OrderByDescending(e => e.CombinedScore).ToList();

        // Calculate technical ranks
        var techRanks = combinedEntries
            .OrderByDescending(e => e.TechScore)
            .Select((e, i) => (e.BidderId, Rank: i + 1))
            .ToDictionary(x => x.BidderId, x => x.Rank);

        // Calculate commercial ranks (from commercial scores)
        var commRanks = latestCommercialScores.Values
            .OrderByDescending(cs => cs.CommercialScoreValue)
            .Select((cs, i) => (cs.BidderId, Rank: i + 1))
            .ToDictionary(x => x.BidderId, x => x.Rank);

        // Remove existing combined scorecards for this tender with same weights
        var existingScorecards = await _context.CombinedScorecards
            .Where(cs => cs.TenderId == request.TenderId)
            .Where(cs => cs.TechnicalWeight == techWeight)
            .Where(cs => cs.CommercialWeight == commWeight)
            .ToListAsync(cancellationToken);

        _context.CombinedScorecards.RemoveRange(existingScorecards);

        // Create new combined scorecards
        var entries = new List<CombinedScoreEntryDto>();
        var now = DateTime.UtcNow;

        for (int i = 0; i < combinedEntries.Count; i++)
        {
            var entry = combinedEntries[i];
            var finalRank = i + 1;
            var isRecommended = finalRank == 1;

            var scorecard = new CombinedScorecard
            {
                TenderId = request.TenderId,
                BidderId = entry.BidderId,
                TechnicalScoreAvg = entry.TechScore,
                TechnicalRank = techRanks[entry.BidderId],
                CommercialScoreValue = entry.CommScore,
                CommercialRank = commRanks[entry.BidderId],
                TechnicalWeight = techWeight,
                CommercialWeight = commWeight,
                CombinedScore = entry.CombinedScore,
                FinalRank = finalRank,
                IsRecommended = isRecommended,
                CalculatedAt = now
            };

            _context.CombinedScorecards.Add(scorecard);

            entries.Add(new CombinedScoreEntryDto
            {
                BidderId = entry.BidderId,
                CompanyName = entry.CompanyName,
                TechnicalScoreAvg = entry.TechScore,
                TechnicalRank = techRanks[entry.BidderId],
                CommercialScoreValue = entry.CommScore,
                CommercialRank = commRanks[entry.BidderId],
                CombinedScore = entry.CombinedScore,
                FinalRank = finalRank,
                IsRecommended = isRecommended,
                TotalPrice = entry.TotalPrice
            });
        }

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Combined scores calculated for tender {TenderId}: {Count} bidders, " +
            "TechWeight: {TechWeight}%, CommWeight: {CommWeight}%",
            request.TenderId, entries.Count, techWeight, commWeight);

        return new CombinedScorecardDto
        {
            TenderId = request.TenderId,
            TenderReference = tender.Reference,
            TenderTitle = tender.Title,
            TechnicalWeight = techWeight,
            CommercialWeight = commWeight,
            Entries = entries,
            CalculatedAt = now
        };
    }
}
