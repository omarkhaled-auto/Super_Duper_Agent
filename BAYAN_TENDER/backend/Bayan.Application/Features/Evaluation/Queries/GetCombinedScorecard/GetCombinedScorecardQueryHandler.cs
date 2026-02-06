using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Queries.GetCombinedScorecard;

/// <summary>
/// Handler for GetCombinedScorecardQuery.
/// </summary>
public class GetCombinedScorecardQueryHandler : IRequestHandler<GetCombinedScorecardQuery, CombinedScorecardDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<GetCombinedScorecardQueryHandler> _logger;

    public GetCombinedScorecardQueryHandler(
        IApplicationDbContext context,
        ILogger<GetCombinedScorecardQueryHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<CombinedScorecardDto> Handle(
        GetCombinedScorecardQuery request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Getting combined scorecard for tender {TenderId} " +
            "(TechWeight: {TechWeight}, CommWeight: {CommWeight})",
            request.TenderId, request.TechnicalWeight, request.CommercialWeight);

        // Get tender
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Determine weights to query
        var techWeight = request.TechnicalWeight ?? tender.TechnicalWeight;
        var commWeight = request.CommercialWeight ?? tender.CommercialWeight;

        // Get existing combined scorecards with matching weights
        var scorecards = await _context.CombinedScorecards
            .Include(cs => cs.Bidder)
            .Where(cs => cs.TenderId == request.TenderId)
            .Where(cs => cs.TechnicalWeight == techWeight)
            .Where(cs => cs.CommercialWeight == commWeight)
            .OrderBy(cs => cs.FinalRank)
            .ToListAsync(cancellationToken);

        if (!scorecards.Any())
        {
            _logger.LogInformation(
                "No combined scorecards found for tender {TenderId} with weights Tech={TechWeight}, Comm={CommWeight}",
                request.TenderId, techWeight, commWeight);

            return new CombinedScorecardDto
            {
                TenderId = request.TenderId,
                TenderReference = tender.Reference,
                TenderTitle = tender.Title,
                TechnicalWeight = techWeight,
                CommercialWeight = commWeight,
                Entries = new List<CombinedScoreEntryDto>(),
                CalculatedAt = DateTime.MinValue
            };
        }

        // Get commercial scores for total prices
        var commercialScores = await _context.CommercialScores
            .Where(cs => cs.TenderId == request.TenderId)
            .GroupBy(cs => cs.BidderId)
            .Select(g => new { BidderId = g.Key, TotalPrice = g.OrderByDescending(x => x.CalculatedAt).First().NormalizedTotalPrice })
            .ToDictionaryAsync(x => x.BidderId, x => x.TotalPrice, cancellationToken);

        var entries = scorecards.Select(sc => new CombinedScoreEntryDto
        {
            BidderId = sc.BidderId,
            CompanyName = sc.Bidder.CompanyName,
            TechnicalScoreAvg = sc.TechnicalScoreAvg,
            TechnicalRank = sc.TechnicalRank,
            CommercialScoreValue = sc.CommercialScoreValue,
            CommercialRank = sc.CommercialRank,
            CombinedScore = sc.CombinedScore,
            FinalRank = sc.FinalRank,
            IsRecommended = sc.IsRecommended,
            TotalPrice = commercialScores.TryGetValue(sc.BidderId, out var price) ? price : 0
        }).ToList();

        return new CombinedScorecardDto
        {
            TenderId = request.TenderId,
            TenderReference = tender.Reference,
            TenderTitle = tender.Title,
            TechnicalWeight = techWeight,
            CommercialWeight = commWeight,
            Entries = entries,
            CalculatedAt = scorecards.First().CalculatedAt
        };
    }
}
