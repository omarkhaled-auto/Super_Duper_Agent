using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Tenders.Commands.UpdateTender;

/// <summary>
/// Command for updating an existing tender.
/// </summary>
public class UpdateTenderCommand : IRequest<TenderDto?>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid Id { get; set; }

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
    /// Note: Cannot be changed if bids have been received.
    /// </summary>
    public string BaseCurrency { get; set; } = "AED";

    /// <summary>
    /// Estimated value of the tender.
    /// </summary>
    public decimal? EstimatedValue { get; set; }

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
