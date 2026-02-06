namespace Bayan.Application.Features.Tenders.DTOs;

/// <summary>
/// Data transfer object for evaluation criterion.
/// </summary>
public class EvaluationCriterionDto
{
    /// <summary>
    /// Unique identifier for the criterion.
    /// </summary>
    public Guid Id { get; set; }

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
}

/// <summary>
/// Data transfer object for creating/updating evaluation criterion.
/// </summary>
public class CreateEvaluationCriterionDto
{
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
}
