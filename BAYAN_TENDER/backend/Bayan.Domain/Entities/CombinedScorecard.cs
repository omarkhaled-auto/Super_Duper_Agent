using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a combined scorecard for a bidder.
/// </summary>
public class CombinedScorecard : BaseEntity
{
    /// <summary>
    /// Tender being evaluated.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder being scored.
    /// </summary>
    public Guid BidderId { get; set; }

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
    /// Technical weight percentage.
    /// </summary>
    public int TechnicalWeight { get; set; }

    /// <summary>
    /// Commercial weight percentage.
    /// </summary>
    public int CommercialWeight { get; set; }

    /// <summary>
    /// Combined weighted score.
    /// </summary>
    public decimal CombinedScore { get; set; }

    /// <summary>
    /// Final rank.
    /// </summary>
    public int FinalRank { get; set; }

    /// <summary>
    /// Whether this bidder is recommended for award.
    /// </summary>
    public bool IsRecommended { get; set; }

    /// <summary>
    /// When the scorecard was calculated.
    /// </summary>
    public DateTime CalculatedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this scorecard.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Bidder being scored.
    /// </summary>
    public virtual Bidder Bidder { get; set; } = null!;
}
