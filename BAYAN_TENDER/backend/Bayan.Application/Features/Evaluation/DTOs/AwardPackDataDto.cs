using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Evaluation.DTOs;

/// <summary>
/// Data transfer object containing all data needed to generate an award pack PDF.
/// </summary>
public class AwardPackDataDto
{
    // Tender Information
    public Guid TenderId { get; set; }
    public string TenderReference { get; set; } = string.Empty;
    public string TenderTitle { get; set; } = string.Empty;
    public string? TenderDescription { get; set; }
    public string ClientName { get; set; } = string.Empty;
    public TenderType TenderType { get; set; }
    public string BaseCurrency { get; set; } = "AED";
    public DateTime IssueDate { get; set; }
    public DateTime SubmissionDeadline { get; set; }
    public int TechnicalWeight { get; set; }
    public int CommercialWeight { get; set; }

    // Evaluation Methodology
    public List<EvaluationCriteriaDto> EvaluationCriteria { get; set; } = new();

    // Technical Evaluation Results
    public List<TechnicalEvaluationResultDto> TechnicalResults { get; set; } = new();

    // Commercial Evaluation Results
    public List<CommercialEvaluationResultDto> CommercialResults { get; set; } = new();

    // Combined Scorecard
    public CombinedScorecardDto? CombinedScorecard { get; set; }

    // Sensitivity Analysis
    public SensitivityAnalysisDto? SensitivityAnalysis { get; set; }

    // Bid Exceptions
    public List<BidExceptionDto> Exceptions { get; set; } = new();

    // Recommendation
    public RecommendationDto? Recommendation { get; set; }

    // Options
    public bool IncludeTechnicalDetails { get; set; } = true;
    public bool IncludeCommercialDetails { get; set; } = true;
    public bool IncludeSensitivityAnalysis { get; set; } = true;
    public bool IncludeExceptions { get; set; } = true;

    // Custom content
    public string? ExecutiveSummary { get; set; }
    public string? RecommendationNotes { get; set; }

    // Generation metadata
    public DateTime GeneratedAt { get; set; }
    public string GeneratedByName { get; set; } = string.Empty;
}

/// <summary>
/// DTO for evaluation criteria in the award pack.
/// </summary>
public class EvaluationCriteriaDto
{
    public string Name { get; set; } = string.Empty;
    public decimal WeightPercentage { get; set; }
    public string? GuidanceNotes { get; set; }
    public int SortOrder { get; set; }
}

/// <summary>
/// DTO for technical evaluation results per bidder.
/// </summary>
public class TechnicalEvaluationResultDto
{
    public Guid BidderId { get; set; }
    public string CompanyName { get; set; } = string.Empty;
    public decimal AverageScore { get; set; }
    public int Rank { get; set; }
    public List<CriteriaScoreDto> CriteriaScores { get; set; } = new();
}

/// <summary>
/// DTO for individual criteria scores.
/// </summary>
public class CriteriaScoreDto
{
    public string CriteriaName { get; set; } = string.Empty;
    public decimal AverageScore { get; set; }
    public decimal WeightedScore { get; set; }
}

/// <summary>
/// DTO for commercial evaluation results per bidder.
/// </summary>
public class CommercialEvaluationResultDto
{
    public Guid BidderId { get; set; }
    public string CompanyName { get; set; } = string.Empty;
    public decimal TotalPrice { get; set; }
    public decimal CommercialScore { get; set; }
    public int Rank { get; set; }
}

/// <summary>
/// DTO for the final recommendation.
/// </summary>
public class RecommendationDto
{
    public Guid RecommendedBidderId { get; set; }
    public string RecommendedBidderName { get; set; } = string.Empty;
    public decimal RecommendedBidAmount { get; set; }
    public decimal CombinedScore { get; set; }
    public int TechnicalRank { get; set; }
    public int CommercialRank { get; set; }
    public string? Notes { get; set; }
}
