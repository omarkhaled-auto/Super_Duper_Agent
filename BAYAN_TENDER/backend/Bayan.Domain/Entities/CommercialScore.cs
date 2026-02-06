using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents an auto-calculated commercial score.
/// </summary>
public class CommercialScore : BaseEntity
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
    /// Normalized total price.
    /// </summary>
    public decimal NormalizedTotalPrice { get; set; }

    /// <summary>
    /// Commercial score (Lowest / This) x 100.
    /// </summary>
    public decimal CommercialScoreValue { get; set; }

    /// <summary>
    /// Rank based on commercial score.
    /// </summary>
    public int Rank { get; set; }

    /// <summary>
    /// Whether provisional sums are included.
    /// </summary>
    public bool IncludeProvisionalSums { get; set; }

    /// <summary>
    /// Whether alternates are included.
    /// </summary>
    public bool IncludeAlternates { get; set; }

    /// <summary>
    /// When the score was calculated.
    /// </summary>
    public DateTime CalculatedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this score.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Bidder being scored.
    /// </summary>
    public virtual Bidder Bidder { get; set; } = null!;
}
