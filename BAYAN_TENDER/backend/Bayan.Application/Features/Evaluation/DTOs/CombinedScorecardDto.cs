using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Evaluation.DTOs;

/// <summary>
/// DTO for an individual bidder's score entry in the combined scorecard.
/// </summary>
public class CombinedScoreEntryDto
{
    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Average technical score.
    /// </summary>
    public decimal TechnicalScoreAvg { get; set; }

    /// <summary>
    /// Technical rank.
    /// </summary>
    public int TechnicalRank { get; set; }

    /// <summary>
    /// Commercial score.
    /// </summary>
    public decimal CommercialScoreValue { get; set; }

    /// <summary>
    /// Commercial rank.
    /// </summary>
    public int CommercialRank { get; set; }

    /// <summary>
    /// Combined weighted score.
    /// Formula: (TechWeight/100 * TechScore) + (CommWeight/100 * CommScore)
    /// </summary>
    public decimal CombinedScore { get; set; }

    /// <summary>
    /// Final rank based on combined score.
    /// </summary>
    public int FinalRank { get; set; }

    /// <summary>
    /// Whether this bidder is recommended for award.
    /// </summary>
    public bool IsRecommended { get; set; }

    /// <summary>
    /// Total bid price.
    /// </summary>
    public decimal TotalPrice { get; set; }
}

/// <summary>
/// DTO for the combined scorecard result.
/// </summary>
public class CombinedScorecardDto
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender reference.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Technical weight percentage used for calculation.
    /// </summary>
    public int TechnicalWeight { get; set; }

    /// <summary>
    /// Commercial weight percentage used for calculation.
    /// </summary>
    public int CommercialWeight { get; set; }

    /// <summary>
    /// List of bidder scores.
    /// </summary>
    public List<CombinedScoreEntryDto> Entries { get; set; } = new();

    /// <summary>
    /// When the scorecard was calculated.
    /// </summary>
    public DateTime CalculatedAt { get; set; }
}

/// <summary>
/// DTO for calculating combined scores request.
/// </summary>
public class CalculateCombinedScoresRequestDto
{
    /// <summary>
    /// Technical weight percentage (default from tender settings).
    /// </summary>
    public int? TechnicalWeight { get; set; }

    /// <summary>
    /// Commercial weight percentage (default from tender settings).
    /// </summary>
    public int? CommercialWeight { get; set; }
}
