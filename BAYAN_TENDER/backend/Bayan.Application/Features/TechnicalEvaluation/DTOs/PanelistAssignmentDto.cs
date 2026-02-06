namespace Bayan.Application.Features.TechnicalEvaluation.DTOs;

/// <summary>
/// DTO representing a panelist's assignments for evaluation.
/// Contains the list of bidders to score and progress tracking.
/// </summary>
public class PanelistAssignmentDto
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
    /// The tender reference number.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Whether blind mode is enabled (bidder names hidden).
    /// </summary>
    public bool BlindMode { get; set; }

    /// <summary>
    /// Deadline for completing technical evaluation.
    /// </summary>
    public DateTime? EvaluationDeadline { get; set; }

    /// <summary>
    /// Whether the deadline has passed.
    /// </summary>
    public bool IsOverdue => EvaluationDeadline.HasValue && EvaluationDeadline.Value < DateTime.UtcNow;

    /// <summary>
    /// Whether technical scores are locked.
    /// </summary>
    public bool TechnicalScoresLocked { get; set; }

    /// <summary>
    /// List of bidders to evaluate.
    /// </summary>
    public List<BidderAssignmentDto> Bidders { get; set; } = new();

    /// <summary>
    /// List of evaluation criteria.
    /// </summary>
    public List<EvaluationCriterionInfoDto> Criteria { get; set; } = new();

    /// <summary>
    /// Number of bidders fully scored (all criteria).
    /// </summary>
    public int BiddersCompleted { get; set; }

    /// <summary>
    /// Total number of bidders to evaluate.
    /// </summary>
    public int TotalBidders { get; set; }

    /// <summary>
    /// Overall progress percentage.
    /// </summary>
    public decimal ProgressPercentage => TotalBidders > 0
        ? Math.Round((decimal)BiddersCompleted / TotalBidders * 100, 1)
        : 0;
}

/// <summary>
/// DTO representing a bidder in the panelist's assignment list.
/// </summary>
public class BidderAssignmentDto
{
    /// <summary>
    /// The bidder's unique identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// The bidder's company name (null if blind mode).
    /// </summary>
    public string? CompanyName { get; set; }

    /// <summary>
    /// Anonymous identifier for the bidder (used in blind mode).
    /// </summary>
    public string AnonymousId { get; set; } = string.Empty;

    /// <summary>
    /// Number of criteria scored for this bidder.
    /// </summary>
    public int CriteriaScored { get; set; }

    /// <summary>
    /// Total number of criteria to score.
    /// </summary>
    public int TotalCriteria { get; set; }

    /// <summary>
    /// Whether all criteria have been scored (draft or final).
    /// </summary>
    public bool HasAllScores => CriteriaScored == TotalCriteria && TotalCriteria > 0;

    /// <summary>
    /// Whether all scores are final (not draft).
    /// </summary>
    public bool IsFullySubmitted { get; set; }

    /// <summary>
    /// Progress percentage for this bidder.
    /// </summary>
    public decimal ProgressPercentage => TotalCriteria > 0
        ? Math.Round((decimal)CriteriaScored / TotalCriteria * 100, 1)
        : 0;

    /// <summary>
    /// List of scores for this bidder (current panelist only).
    /// </summary>
    public List<TechnicalScoreDto> Scores { get; set; } = new();
}
