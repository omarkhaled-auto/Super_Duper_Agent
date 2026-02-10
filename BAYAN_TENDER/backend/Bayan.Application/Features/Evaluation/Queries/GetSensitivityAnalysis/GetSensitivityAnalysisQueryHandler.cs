using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Queries.GetSensitivityAnalysis;

/// <summary>
/// Handler for GetSensitivityAnalysisQuery.
/// Runs calculations for 9 weight splits (30/70 through 70/30 in 5% increments).
/// </summary>
public class GetSensitivityAnalysisQueryHandler : IRequestHandler<GetSensitivityAnalysisQuery, SensitivityAnalysisDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<GetSensitivityAnalysisQueryHandler> _logger;

    // Standard weight splits to analyze (Tech/Comm)
    private static readonly (int Tech, int Comm, string Label)[] WeightSplits =
    {
        (30, 70, "30/70"),
        (35, 65, "35/65"),
        (40, 60, "40/60"),
        (45, 55, "45/55"),
        (50, 50, "50/50"),
        (55, 45, "55/45"),
        (60, 40, "60/40"),
        (65, 35, "65/35"),
        (70, 30, "70/30")
    };

    public GetSensitivityAnalysisQueryHandler(
        IApplicationDbContext context,
        ILogger<GetSensitivityAnalysisQueryHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<SensitivityAnalysisDto> Handle(
        GetSensitivityAnalysisQuery request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Running sensitivity analysis for tender {TenderId}", request.TenderId);

        // Get tender
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Get technical scores (average of submitted scores per bidder)
        var technicalScoresByBidder = await _context.TechnicalScores
            .Where(ts => ts.TenderId == request.TenderId)
            .Where(ts => !ts.IsDraft)
            .GroupBy(ts => ts.BidderId)
            .Select(g => new
            {
                BidderId = g.Key,
                AverageScore = g.Average(ts => ts.Score)
            })
            .ToDictionaryAsync(x => x.BidderId, x => x.AverageScore, cancellationToken);

        // Get commercial scores with bidder info
        var commercialScores = await _context.CommercialScores
            .Include(cs => cs.Bidder)
            .Where(cs => cs.TenderId == request.TenderId)
            .GroupBy(cs => cs.BidderId)
            .Select(g => g.OrderByDescending(x => x.CalculatedAt).First())
            .ToListAsync(cancellationToken);

        if (!commercialScores.Any())
        {
            _logger.LogWarning("No commercial scores found for tender {TenderId}", request.TenderId);
            return new SensitivityAnalysisDto
            {
                TenderId = request.TenderId,
                TenderReference = tender.Reference,
                TenderTitle = tender.Title,
                WeightSplits = WeightSplits.Select(w => w.Label).ToList(),
                Rows = new List<SensitivityRowDto>(),
                WinnerChanges = false,
                WinnerByWeightSplit = new Dictionary<string, string>(),
                GeneratedAt = DateTime.UtcNow
            };
        }

        // Build bidder data with both scores
        var bidderData = commercialScores.Select(cs => new
        {
            BidderId = cs.BidderId,
            CompanyName = cs.Bidder.CompanyName,
            TechScore = technicalScoresByBidder.TryGetValue(cs.BidderId, out var ts) ? ts : 0m,
            CommScore = cs.CommercialScoreValue
        }).ToList();

        // Calculate combined scores and ranks for each weight split
        var rows = new List<SensitivityRowDto>();
        var winnerByWeightSplit = new Dictionary<string, string>();

        foreach (var bidder in bidderData)
        {
            var row = new SensitivityRowDto
            {
                BidderId = bidder.BidderId,
                CompanyName = bidder.CompanyName,
                TechnicalScore = bidder.TechScore,
                CommercialScore = bidder.CommScore,
                RanksByWeightSplit = new Dictionary<string, int>(),
                ScoresByWeightSplit = new Dictionary<string, decimal>()
            };

            foreach (var (tech, comm, label) in WeightSplits)
            {
                var combinedScore = (tech / 100m * bidder.TechScore) + (comm / 100m * bidder.CommScore);
                row.ScoresByWeightSplit[label] = Math.Round(combinedScore, 2);
            }

            rows.Add(row);
        }

        // Calculate ranks for each weight split
        foreach (var (_, _, label) in WeightSplits)
        {
            var rankedBidders = rows
                .OrderByDescending(r => r.ScoresByWeightSplit[label])
                .ToList();

            for (int i = 0; i < rankedBidders.Count; i++)
            {
                rankedBidders[i].RanksByWeightSplit[label] = i + 1;
            }

            // Record winner for this weight split
            if (rankedBidders.Any())
            {
                winnerByWeightSplit[label] = rankedBidders[0].CompanyName;
            }
        }

        // Determine if any bidder has rank variation
        foreach (var row in rows)
        {
            var ranks = row.RanksByWeightSplit.Values.Distinct().ToList();
            row.HasRankVariation = ranks.Count > 1;
        }

        // Check if winner changes across weight splits
        var uniqueWinners = winnerByWeightSplit.Values.Distinct().ToList();
        var winnerChanges = uniqueWinners.Count > 1;

        _logger.LogInformation(
            "Sensitivity analysis completed for tender {TenderId}: {BidderCount} bidders, winner changes: {WinnerChanges}",
            request.TenderId, rows.Count, winnerChanges);

        return new SensitivityAnalysisDto
        {
            TenderId = request.TenderId,
            TenderReference = tender.Reference,
            TenderTitle = tender.Title,
            WeightSplits = WeightSplits.Select(w => w.Label).ToList(),
            Rows = rows.OrderBy(r => r.RanksByWeightSplit.Values.Min()).ToList(),
            WinnerChanges = winnerChanges,
            WinnerByWeightSplit = winnerByWeightSplit,
            GeneratedAt = DateTime.UtcNow
        };
    }
}
