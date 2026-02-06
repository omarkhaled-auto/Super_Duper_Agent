using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents evaluation criteria for a tender.
/// </summary>
public class EvaluationCriteria : BaseEntity
{
    /// <summary>
    /// Tender this criteria belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Name of the evaluation criterion.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Weight percentage for this criterion.
    /// </summary>
    public decimal WeightPercentage { get; set; }

    /// <summary>
    /// Guidance notes for evaluators.
    /// </summary>
    public string? GuidanceNotes { get; set; }

    /// <summary>
    /// Sort order for display.
    /// </summary>
    public int SortOrder { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this criteria.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Technical scores for this criterion.
    /// </summary>
    public virtual ICollection<TechnicalScore> TechnicalScores { get; set; } = new List<TechnicalScore>();
}
