namespace Bayan.Application.Features.TechnicalEvaluation.DTOs;

/// <summary>
/// DTO representing a technical score given by a panelist.
/// </summary>
public class TechnicalScoreDto
{
    /// <summary>
    /// The score record's unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The bidder's unique identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// The bidder's company name (hidden in blind mode).
    /// </summary>
    public string? BidderName { get; set; }

    /// <summary>
    /// Anonymous identifier for bidder in blind mode.
    /// </summary>
    public string? AnonymousId { get; set; }

    /// <summary>
    /// The panelist's unique identifier.
    /// </summary>
    public Guid PanelistUserId { get; set; }

    /// <summary>
    /// The panelist's name.
    /// </summary>
    public string? PanelistName { get; set; }

    /// <summary>
    /// The criterion's unique identifier.
    /// </summary>
    public Guid CriterionId { get; set; }

    /// <summary>
    /// The criterion name.
    /// </summary>
    public string CriterionName { get; set; } = string.Empty;

    /// <summary>
    /// The criterion weight percentage.
    /// </summary>
    public decimal CriterionWeight { get; set; }

    /// <summary>
    /// The score value (0-10 scale).
    /// </summary>
    public decimal Score { get; set; }

    /// <summary>
    /// The weighted score (Score * CriterionWeight / 100).
    /// </summary>
    public decimal WeightedScore => Score * CriterionWeight / 100;

    /// <summary>
    /// Comment/justification for the score.
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
