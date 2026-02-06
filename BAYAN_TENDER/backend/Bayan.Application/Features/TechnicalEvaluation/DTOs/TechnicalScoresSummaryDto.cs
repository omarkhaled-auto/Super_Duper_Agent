namespace Bayan.Application.Features.TechnicalEvaluation.DTOs;

/// <summary>
/// DTO representing the technical scores summary with matrix view, averages, variance, and ranks.
/// </summary>
public class TechnicalScoresSummaryDto
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Whether technical scores are locked.
    /// </summary>
    public bool TechnicalScoresLocked { get; set; }

    /// <summary>
    /// When technical scores were locked.
    /// </summary>
    public DateTime? LockedAt { get; set; }

    /// <summary>
    /// List of evaluation criteria for the matrix header.
    /// </summary>
    public List<CriteriaSummaryDto> Criteria { get; set; } = new();

    /// <summary>
    /// List of panelists who participated in scoring.
    /// </summary>
    public List<PanelistSummaryDto> Panelists { get; set; } = new();

    /// <summary>
    /// Bidder scores matrix with detailed breakdown.
    /// </summary>
    public List<BidderScoresSummaryDto> BidderScores { get; set; } = new();

    /// <summary>
    /// Number of panelists who have completed scoring.
    /// </summary>
    public int CompletedPanelistCount { get; set; }

    /// <summary>
    /// Total number of panelists assigned.
    /// </summary>
    public int TotalPanelistCount { get; set; }

    /// <summary>
    /// Whether all panelists have completed scoring.
    /// </summary>
    public bool AllPanelistsComplete => CompletedPanelistCount == TotalPanelistCount && TotalPanelistCount > 0;
}

/// <summary>
/// DTO for criterion summary in the scores matrix.
/// </summary>
public class CriteriaSummaryDto
{
    /// <summary>
    /// The criterion's unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Name of the criterion.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Weight percentage for this criterion.
    /// </summary>
    public decimal WeightPercentage { get; set; }

    /// <summary>
    /// Display order.
    /// </summary>
    public int SortOrder { get; set; }
}

/// <summary>
/// DTO for panelist summary in the scores matrix.
/// </summary>
public class PanelistSummaryDto
{
    /// <summary>
    /// The panelist's user ID.
    /// </summary>
    public Guid UserId { get; set; }

    /// <summary>
    /// The panelist's full name.
    /// </summary>
    public string FullName { get; set; } = string.Empty;

    /// <summary>
    /// Whether the panelist has completed all scoring.
    /// </summary>
    public bool HasCompletedScoring { get; set; }
}

/// <summary>
/// DTO representing a bidder's scores summary across all criteria and panelists.
/// </summary>
public class BidderScoresSummaryDto
{
    /// <summary>
    /// The bidder's unique identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// The bidder's company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Anonymous identifier for blind mode display.
    /// </summary>
    public string AnonymousId { get; set; } = string.Empty;

    /// <summary>
    /// Scores per criterion (average across all panelists).
    /// </summary>
    public List<CriterionScoreAverageDto> CriterionScores { get; set; } = new();

    /// <summary>
    /// Detailed scores from each panelist for each criterion.
    /// </summary>
    public List<PanelistCriterionScoreDto> PanelistScores { get; set; } = new();

    /// <summary>
    /// Total weighted score (sum of weighted criterion averages).
    /// </summary>
    public decimal TotalWeightedScore { get; set; }

    /// <summary>
    /// Variance in total scores across panelists.
    /// </summary>
    public decimal ScoreVariance { get; set; }

    /// <summary>
    /// Standard deviation of scores across panelists.
    /// </summary>
    public decimal StandardDeviation { get; set; }

    /// <summary>
    /// Rank based on total weighted score (1 = highest).
    /// </summary>
    public int Rank { get; set; }

    /// <summary>
    /// Number of panelists who have scored this bidder.
    /// </summary>
    public int PanelistsScored { get; set; }

    /// <summary>
    /// Whether all assigned panelists have scored this bidder.
    /// </summary>
    public bool IsFullyScored { get; set; }
}

/// <summary>
/// DTO for criterion score average across all panelists.
/// </summary>
public class CriterionScoreAverageDto
{
    /// <summary>
    /// The criterion's unique identifier.
    /// </summary>
    public Guid CriterionId { get; set; }

    /// <summary>
    /// Name of the criterion.
    /// </summary>
    public string CriterionName { get; set; } = string.Empty;

    /// <summary>
    /// Weight percentage for this criterion.
    /// </summary>
    public decimal WeightPercentage { get; set; }

    /// <summary>
    /// Average raw score across all panelists (0-10 scale).
    /// </summary>
    public decimal AverageScore { get; set; }

    /// <summary>
    /// Weighted average score (AverageScore * WeightPercentage / 100).
    /// </summary>
    public decimal WeightedAverageScore { get; set; }

    /// <summary>
    /// Minimum score given by any panelist.
    /// </summary>
    public decimal MinScore { get; set; }

    /// <summary>
    /// Maximum score given by any panelist.
    /// </summary>
    public decimal MaxScore { get; set; }

    /// <summary>
    /// Variance in scores for this criterion.
    /// </summary>
    public decimal Variance { get; set; }
}

/// <summary>
/// DTO for individual panelist's score on a specific criterion for a bidder.
/// </summary>
public class PanelistCriterionScoreDto
{
    /// <summary>
    /// The panelist's user ID.
    /// </summary>
    public Guid PanelistUserId { get; set; }

    /// <summary>
    /// The panelist's name.
    /// </summary>
    public string PanelistName { get; set; } = string.Empty;

    /// <summary>
    /// The criterion's unique identifier.
    /// </summary>
    public Guid CriterionId { get; set; }

    /// <summary>
    /// The criterion name.
    /// </summary>
    public string CriterionName { get; set; } = string.Empty;

    /// <summary>
    /// The raw score (0-10 scale).
    /// </summary>
    public decimal Score { get; set; }

    /// <summary>
    /// Comment/justification.
    /// </summary>
    public string? Comment { get; set; }

    /// <summary>
    /// Whether this is a draft score.
    /// </summary>
    public bool IsDraft { get; set; }

    /// <summary>
    /// When the score was submitted.
    /// </summary>
    public DateTime? SubmittedAt { get; set; }
}
