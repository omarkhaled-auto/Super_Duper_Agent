namespace Bayan.Application.Features.Evaluation.DTOs;

/// <summary>
/// DTO for a single row in the sensitivity analysis showing a bidder's rank at different weight splits.
/// </summary>
public class SensitivityRowDto
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
    /// Technical score average.
    /// </summary>
    public decimal TechnicalScore { get; set; }

    /// <summary>
    /// Commercial score.
    /// </summary>
    public decimal CommercialScore { get; set; }

    /// <summary>
    /// Dictionary of weight split label to rank.
    /// Keys: "30/70", "40/60", "50/50", "60/40", "70/30"
    /// Values: Rank at that weight split.
    /// </summary>
    public Dictionary<string, int> RanksByWeightSplit { get; set; } = new();

    /// <summary>
    /// Dictionary of weight split label to combined score.
    /// Keys: "30/70", "40/60", "50/50", "60/40", "70/30"
    /// Values: Combined score at that weight split.
    /// </summary>
    public Dictionary<string, decimal> ScoresByWeightSplit { get; set; } = new();

    /// <summary>
    /// Whether the rank changes across different weight splits.
    /// </summary>
    public bool HasRankVariation { get; set; }
}

/// <summary>
/// DTO for the complete sensitivity analysis result.
/// </summary>
public class SensitivityAnalysisDto
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
    /// Weight splits analyzed (Tech/Comm).
    /// Example: ["30/70", "40/60", "50/50", "60/40", "70/30"]
    /// </summary>
    public List<string> WeightSplits { get; set; } = new();

    /// <summary>
    /// Bidder rows with rank changes.
    /// </summary>
    public List<SensitivityRowDto> Rows { get; set; } = new();

    /// <summary>
    /// Whether the winner changes across different weight splits.
    /// </summary>
    public bool WinnerChanges { get; set; }

    /// <summary>
    /// Summary of which bidder wins at which weight splits.
    /// </summary>
    public Dictionary<string, string> WinnerByWeightSplit { get; set; } = new();

    /// <summary>
    /// When the analysis was generated.
    /// </summary>
    public DateTime GeneratedAt { get; set; }
}
