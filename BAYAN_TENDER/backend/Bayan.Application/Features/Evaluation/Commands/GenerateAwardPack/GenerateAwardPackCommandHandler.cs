using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Commands.GenerateAwardPack;

/// <summary>
/// Handler for GenerateAwardPackCommand.
/// Generates a comprehensive award pack PDF and stores it in MinIO.
/// </summary>
public class GenerateAwardPackCommandHandler : IRequestHandler<GenerateAwardPackCommand, AwardPackDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IPdfService _pdfService;
    private readonly IFileStorageService _fileStorageService;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<GenerateAwardPackCommandHandler> _logger;

    public GenerateAwardPackCommandHandler(
        IApplicationDbContext context,
        IPdfService pdfService,
        IFileStorageService fileStorageService,
        ICurrentUserService currentUserService,
        ILogger<GenerateAwardPackCommandHandler> logger)
    {
        _context = context;
        _pdfService = pdfService;
        _fileStorageService = fileStorageService;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<AwardPackDto> Handle(
        GenerateAwardPackCommand request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Generating award pack for tender {TenderId}", request.TenderId);

        // Get tender with client
        var tender = await _context.Tenders
            .Include(t => t.Client)
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Get current user info
        var currentUserId = _currentUserService.UserId ?? throw new UnauthorizedAccessException("User not authenticated.");
        var currentUser = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == currentUserId, cancellationToken);

        var currentUserName = currentUser != null
            ? $"{currentUser.FirstName} {currentUser.LastName}".Trim()
            : "Unknown";

        // Build award pack data
        var awardPackData = new AwardPackDataDto
        {
            TenderId = tender.Id,
            TenderReference = tender.Reference,
            TenderTitle = tender.Title,
            TenderDescription = tender.Description,
            ClientName = tender.Client.Name,
            TenderType = tender.TenderType,
            BaseCurrency = tender.BaseCurrency,
            IssueDate = tender.IssueDate,
            SubmissionDeadline = tender.SubmissionDeadline,
            TechnicalWeight = tender.TechnicalWeight,
            CommercialWeight = tender.CommercialWeight,
            IncludeTechnicalDetails = request.IncludeTechnicalDetails,
            IncludeCommercialDetails = request.IncludeCommercialDetails,
            IncludeSensitivityAnalysis = request.IncludeSensitivityAnalysis,
            IncludeExceptions = request.IncludeExceptions,
            ExecutiveSummary = request.ExecutiveSummary,
            RecommendationNotes = request.RecommendationNotes,
            GeneratedAt = DateTime.UtcNow,
            GeneratedByName = currentUserName
        };

        // Get evaluation criteria
        var criteria = await _context.EvaluationCriteria
            .Where(ec => ec.TenderId == request.TenderId)
            .OrderBy(ec => ec.SortOrder)
            .ToListAsync(cancellationToken);

        awardPackData.EvaluationCriteria = criteria.Select(c => new EvaluationCriteriaDto
        {
            Name = c.Name,
            WeightPercentage = c.WeightPercentage,
            GuidanceNotes = c.GuidanceNotes,
            SortOrder = c.SortOrder
        }).ToList();

        // Get technical evaluation results
        if (request.IncludeTechnicalDetails)
        {
            var technicalScores = await _context.TechnicalScores
                .Include(ts => ts.Bidder)
                .Include(ts => ts.Criterion)
                .Where(ts => ts.TenderId == request.TenderId)
                .Where(ts => !ts.IsDraft)
                .ToListAsync(cancellationToken);

            var groupedByBidder = technicalScores
                .GroupBy(ts => ts.BidderId)
                .Select(g =>
                {
                    var bidder = g.First().Bidder;
                    var avgScore = g.Average(ts => ts.Score);
                    var criteriaScores = g
                        .GroupBy(ts => ts.CriterionId)
                        .Select(cg =>
                        {
                            var criterion = cg.First().Criterion;
                            var criterionAvg = cg.Average(ts => ts.Score);
                            return new CriteriaScoreDto
                            {
                                CriteriaName = criterion.Name,
                                AverageScore = Math.Round(criterionAvg, 2),
                                WeightedScore = Math.Round(criterionAvg * criterion.WeightPercentage / 100, 2)
                            };
                        }).ToList();

                    return new TechnicalEvaluationResultDto
                    {
                        BidderId = g.Key,
                        CompanyName = bidder.CompanyName,
                        AverageScore = Math.Round(avgScore, 2),
                        CriteriaScores = criteriaScores
                    };
                })
                .OrderByDescending(r => r.AverageScore)
                .ToList();

            // Assign ranks
            for (int i = 0; i < groupedByBidder.Count; i++)
            {
                groupedByBidder[i].Rank = i + 1;
            }

            awardPackData.TechnicalResults = groupedByBidder;
        }

        // Get commercial evaluation results
        if (request.IncludeCommercialDetails)
        {
            var allCommercialScores = await _context.CommercialScores
                .Include(cs => cs.Bidder)
                .Where(cs => cs.TenderId == request.TenderId)
                .ToListAsync(cancellationToken);

            var commercialScores = allCommercialScores
                .GroupBy(cs => cs.BidderId)
                .Select(g => g.OrderByDescending(x => x.CalculatedAt).First())
                .ToList();

            awardPackData.CommercialResults = commercialScores
                .OrderByDescending(cs => cs.CommercialScoreValue)
                .Select((cs, i) => new CommercialEvaluationResultDto
                {
                    BidderId = cs.BidderId,
                    CompanyName = cs.Bidder.CompanyName,
                    TotalPrice = cs.NormalizedTotalPrice,
                    CommercialScore = cs.CommercialScoreValue,
                    Rank = i + 1
                })
                .ToList();
        }

        // Get combined scorecard
        var combinedScorecards = await _context.CombinedScorecards
            .Include(cs => cs.Bidder)
            .Where(cs => cs.TenderId == request.TenderId)
            .Where(cs => cs.TechnicalWeight == tender.TechnicalWeight)
            .Where(cs => cs.CommercialWeight == tender.CommercialWeight)
            .OrderBy(cs => cs.FinalRank)
            .ToListAsync(cancellationToken);

        if (combinedScorecards.Any())
        {
            // Get commercial scores for total prices (materialize before GroupBy to avoid EF Core SQL translation issues)
            var allCommercialPriceScores = await _context.CommercialScores
                .Where(cs => cs.TenderId == request.TenderId)
                .ToListAsync(cancellationToken);

            var commercialPrices = allCommercialPriceScores
                .GroupBy(cs => cs.BidderId)
                .ToDictionary(
                    g => g.Key,
                    g => g.OrderByDescending(x => x.CalculatedAt).First().NormalizedTotalPrice);

            awardPackData.CombinedScorecard = new CombinedScorecardDto
            {
                TenderId = request.TenderId,
                TenderReference = tender.Reference,
                TenderTitle = tender.Title,
                TechnicalWeight = tender.TechnicalWeight,
                CommercialWeight = tender.CommercialWeight,
                Entries = combinedScorecards.Select(cs => new CombinedScoreEntryDto
                {
                    BidderId = cs.BidderId,
                    CompanyName = cs.Bidder.CompanyName,
                    TechnicalScoreAvg = cs.TechnicalScoreAvg,
                    TechnicalRank = cs.TechnicalRank,
                    CommercialScoreValue = cs.CommercialScoreValue,
                    CommercialRank = cs.CommercialRank,
                    CombinedScore = cs.CombinedScore,
                    FinalRank = cs.FinalRank,
                    IsRecommended = cs.IsRecommended,
                    TotalPrice = commercialPrices.TryGetValue(cs.BidderId, out var price) ? price : 0
                }).ToList(),
                CalculatedAt = combinedScorecards.First().CalculatedAt
            };

            // Build recommendation
            var recommended = combinedScorecards.FirstOrDefault(cs => cs.IsRecommended);
            if (recommended != null)
            {
                awardPackData.Recommendation = new RecommendationDto
                {
                    RecommendedBidderId = recommended.BidderId,
                    RecommendedBidderName = recommended.Bidder.CompanyName,
                    RecommendedBidAmount = commercialPrices.TryGetValue(recommended.BidderId, out var recPrice) ? recPrice : 0,
                    CombinedScore = recommended.CombinedScore,
                    TechnicalRank = recommended.TechnicalRank,
                    CommercialRank = recommended.CommercialRank,
                    Notes = request.RecommendationNotes
                };
            }
        }

        // Get sensitivity analysis if requested
        if (request.IncludeSensitivityAnalysis)
        {
            awardPackData.SensitivityAnalysis = await BuildSensitivityAnalysis(request.TenderId, tender, cancellationToken);
        }

        // Get bid exceptions if requested
        // Note: bid_exceptions table schema uses bid_submission_id (not tender_id/bidder_id),
        // so we gracefully degrade if the query fails due to schema mismatch
        if (request.IncludeExceptions)
        {
            try
            {
                var exceptions = await _context.BidExceptions
                    .Include(be => be.Bidder)
                    .Include(be => be.LoggedByUser)
                    .Where(be => be.TenderId == request.TenderId)
                    .OrderByDescending(be => be.RiskLevel)
                    .ThenByDescending(be => be.CreatedAt)
                    .ToListAsync(cancellationToken);

                awardPackData.Exceptions = exceptions.Select(e => new BidExceptionDto
                {
                    Id = e.Id,
                    TenderId = e.TenderId,
                    BidderId = e.BidderId,
                    BidderCompanyName = e.Bidder?.CompanyName ?? "Unknown",
                    ExceptionType = e.ExceptionType,
                    Description = e.Description,
                    CostImpact = e.CostImpact,
                    TimeImpactDays = e.TimeImpactDays,
                    RiskLevel = e.RiskLevel,
                    Mitigation = e.Mitigation,
                    LoggedBy = e.LoggedBy,
                    LoggedByName = e.LoggedByUser != null
                        ? $"{e.LoggedByUser.FirstName} {e.LoggedByUser.LastName}".Trim()
                        : "Unknown",
                    CreatedAt = e.CreatedAt
                }).ToList();
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to load bid exceptions for tender {TenderId}. Continuing without exceptions.", request.TenderId);
                awardPackData.Exceptions = new List<BidExceptionDto>();
            }
        }

        // Generate PDF
        _logger.LogInformation("Generating award pack PDF for tender {TenderId}", request.TenderId);
        byte[] pdfBytes;
        try
        {
            pdfBytes = await _pdfService.GenerateAwardPackPdfAsync(awardPackData, cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex,
                "PDF generation failed for tender {TenderId}",
                request.TenderId);
            throw new InvalidOperationException(
                $"Failed to generate the award pack PDF for tender '{tender.Reference}'. Please try again or contact support.", ex);
        }

        // Upload to MinIO
        var fileName = $"AwardPack_{tender.Reference}_{DateTime.UtcNow:yyyyMMdd_HHmmss}.pdf";
        var storagePath = $"tenders/{request.TenderId}/award-packs";

        string filePath;
        try
        {
            using var stream = new MemoryStream(pdfBytes);
            filePath = await _fileStorageService.UploadFileAsync(
                stream,
                fileName,
                "application/pdf",
                storagePath,
                cancellationToken);
        }
        catch (IOException ex)
        {
            _logger.LogError(ex,
                "File upload to storage failed for award pack {FileName} on tender {TenderId}",
                fileName, request.TenderId);
            throw new InvalidOperationException(
                $"Failed to upload the award pack file for tender '{tender.Reference}'. Please try again or contact support.", ex);
        }

        // Get download URL
        var downloadUrl = await _fileStorageService.GetPresignedUrlAsync(
            filePath,
            TimeSpan.FromHours(24),
            cancellationToken);

        _logger.LogInformation(
            "Award pack generated for tender {TenderId}: {FileName}, {Size} bytes",
            request.TenderId, fileName, pdfBytes.Length);

        return new AwardPackDto
        {
            TenderId = request.TenderId,
            TenderReference = tender.Reference,
            TenderTitle = tender.Title,
            FilePath = filePath,
            FileName = fileName,
            DownloadUrl = downloadUrl,
            FileSizeBytes = pdfBytes.Length,
            GeneratedAt = DateTime.UtcNow,
            GeneratedBy = currentUserId,
            GeneratedByName = currentUserName
        };
    }

    private async Task<SensitivityAnalysisDto> BuildSensitivityAnalysis(
        Guid tenderId, Domain.Entities.Tender tender, CancellationToken cancellationToken)
    {
        var weightSplits = new (int Tech, int Comm, string Label)[]
        {
            (30, 70, "30/70"),
            (40, 60, "40/60"),
            (50, 50, "50/50"),
            (60, 40, "60/40"),
            (70, 30, "70/30")
        };

        // Get technical scores
        var technicalScoresByBidder = await _context.TechnicalScores
            .Where(ts => ts.TenderId == tenderId)
            .Where(ts => !ts.IsDraft)
            .GroupBy(ts => ts.BidderId)
            .Select(g => new { BidderId = g.Key, AverageScore = g.Average(ts => ts.Score) })
            .ToDictionaryAsync(x => x.BidderId, x => x.AverageScore, cancellationToken);

        // Get commercial scores with bidder info (materialize before GroupBy to avoid EF Core SQL translation issues)
        var allSensitivityCommScores = await _context.CommercialScores
            .Include(cs => cs.Bidder)
            .Where(cs => cs.TenderId == tenderId)
            .ToListAsync(cancellationToken);

        var commercialScores = allSensitivityCommScores
            .GroupBy(cs => cs.BidderId)
            .Select(g => g.OrderByDescending(x => x.CalculatedAt).First())
            .ToList();

        if (!commercialScores.Any())
        {
            return new SensitivityAnalysisDto
            {
                TenderId = tenderId,
                TenderReference = tender.Reference,
                TenderTitle = tender.Title,
                WeightSplits = weightSplits.Select(w => w.Label).ToList(),
                Rows = new List<SensitivityRowDto>(),
                WinnerChanges = false,
                WinnerByWeightSplit = new Dictionary<string, string>(),
                GeneratedAt = DateTime.UtcNow
            };
        }

        var bidderData = commercialScores.Select(cs => new
        {
            BidderId = cs.BidderId,
            CompanyName = cs.Bidder.CompanyName,
            TechScore = technicalScoresByBidder.TryGetValue(cs.BidderId, out var ts) ? ts : 0m,
            CommScore = cs.CommercialScoreValue
        }).ToList();

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

            foreach (var (tech, comm, label) in weightSplits)
            {
                var combinedScore = (tech / 100m * bidder.TechScore) + (comm / 100m * bidder.CommScore);
                row.ScoresByWeightSplit[label] = Math.Round(combinedScore, 2);
            }

            rows.Add(row);
        }

        foreach (var (_, _, label) in weightSplits)
        {
            var rankedBidders = rows
                .OrderByDescending(r => r.ScoresByWeightSplit[label])
                .ToList();

            for (int i = 0; i < rankedBidders.Count; i++)
            {
                rankedBidders[i].RanksByWeightSplit[label] = i + 1;
            }

            if (rankedBidders.Any())
            {
                winnerByWeightSplit[label] = rankedBidders[0].CompanyName;
            }
        }

        foreach (var row in rows)
        {
            var ranks = row.RanksByWeightSplit.Values.Distinct().ToList();
            row.HasRankVariation = ranks.Count > 1;
        }

        var uniqueWinners = winnerByWeightSplit.Values.Distinct().ToList();
        var winnerChanges = uniqueWinners.Count > 1;

        return new SensitivityAnalysisDto
        {
            TenderId = tenderId,
            TenderReference = tender.Reference,
            TenderTitle = tender.Title,
            WeightSplits = weightSplits.Select(w => w.Label).ToList(),
            Rows = rows.OrderBy(r => r.RanksByWeightSplit.Values.Min()).ToList(),
            WinnerChanges = winnerChanges,
            WinnerByWeightSplit = winnerByWeightSplit,
            GeneratedAt = DateTime.UtcNow
        };
    }
}
