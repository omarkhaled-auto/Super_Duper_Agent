using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Approval.DTOs;

/// <summary>
/// Data transfer object for approval workflow.
/// </summary>
public class ApprovalWorkflowDto
{
    /// <summary>
    /// Workflow ID.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Tender ID associated with this workflow.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender reference number.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Current workflow status.
    /// </summary>
    public ApprovalWorkflowStatus Status { get; set; }

    /// <summary>
    /// User ID who initiated the workflow.
    /// </summary>
    public Guid InitiatedBy { get; set; }

    /// <summary>
    /// Name of the user who initiated the workflow.
    /// </summary>
    public string InitiatedByName { get; set; } = string.Empty;

    /// <summary>
    /// When the workflow was initiated.
    /// </summary>
    public DateTime InitiatedAt { get; set; }

    /// <summary>
    /// When the workflow was completed (if completed).
    /// </summary>
    public DateTime? CompletedAt { get; set; }

    /// <summary>
    /// Path to award pack PDF in MinIO.
    /// </summary>
    public string? AwardPackPdfPath { get; set; }

    /// <summary>
    /// Current active level number.
    /// </summary>
    public int CurrentLevel { get; set; }

    /// <summary>
    /// Total number of levels in the workflow.
    /// </summary>
    public int TotalLevels { get; set; }

    /// <summary>
    /// Approval levels in this workflow.
    /// </summary>
    public List<ApprovalLevelDto> Levels { get; set; } = new();
}
