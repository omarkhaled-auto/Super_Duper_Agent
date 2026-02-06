using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Tenders.DTOs;

/// <summary>
/// Data transfer object for updating an existing tender.
/// </summary>
public class UpdateTenderDto
{
    /// <summary>
    /// Tender title.
    /// </summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Tender description.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Client issuing the tender.
    /// </summary>
    public Guid ClientId { get; set; }

    /// <summary>
    /// Type of tender procedure.
    /// </summary>
    public TenderType TenderType { get; set; }

    /// <summary>
    /// Base currency for the tender (ISO 4217 code).
    /// Note: Currency cannot be changed if bids have been received.
    /// </summary>
    public string BaseCurrency { get; set; } = "AED";

    /// <summary>
    /// Number of days the bid is valid.
    /// </summary>
    public int BidValidityDays { get; set; }

    /// <summary>
    /// Date the tender was issued.
    /// </summary>
    public DateTime IssueDate { get; set; }

    /// <summary>
    /// Deadline for clarification questions.
    /// </summary>
    public DateTime ClarificationDeadline { get; set; }

    /// <summary>
    /// Deadline for bid submissions.
    /// </summary>
    public DateTime SubmissionDeadline { get; set; }

    /// <summary>
    /// Date when bids will be opened.
    /// </summary>
    public DateTime OpeningDate { get; set; }

    /// <summary>
    /// Weight for technical evaluation (percentage).
    /// </summary>
    public int TechnicalWeight { get; set; }

    /// <summary>
    /// Weight for commercial evaluation (percentage).
    /// </summary>
    public int CommercialWeight { get; set; }

    /// <summary>
    /// Evaluation criteria for this tender.
    /// </summary>
    public List<UpdateEvaluationCriterionDto> EvaluationCriteria { get; set; } = new();
}

/// <summary>
/// Data transfer object for updating evaluation criterion.
/// </summary>
public class UpdateEvaluationCriterionDto
{
    /// <summary>
    /// Criterion ID. If null, a new criterion will be created.
    /// </summary>
    public Guid? Id { get; set; }

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
