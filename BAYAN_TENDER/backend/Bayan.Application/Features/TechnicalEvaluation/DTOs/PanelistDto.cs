namespace Bayan.Application.Features.TechnicalEvaluation.DTOs;

/// <summary>
/// DTO representing a panelist assigned to evaluate a tender.
/// </summary>
public class PanelistDto
{
    /// <summary>
    /// The evaluation panel record's unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// The panelist user's unique identifier.
    /// </summary>
    public Guid UserId { get; set; }

    /// <summary>
    /// The panelist's full name.
    /// </summary>
    public string FullName { get; set; } = string.Empty;

    /// <summary>
    /// The panelist's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// The panelist's department.
    /// </summary>
    public string? Department { get; set; }

    /// <summary>
    /// The panelist's job title.
    /// </summary>
    public string? JobTitle { get; set; }

    /// <summary>
    /// When the panelist was assigned.
    /// </summary>
    public DateTime AssignedAt { get; set; }

    /// <summary>
    /// When the panelist completed their evaluation (all scores submitted).
    /// </summary>
    public DateTime? CompletedAt { get; set; }

    /// <summary>
    /// Number of bidders scored by this panelist.
    /// </summary>
    public int BiddersScored { get; set; }

    /// <summary>
    /// Total number of bidders to score.
    /// </summary>
    public int TotalBidders { get; set; }

    /// <summary>
    /// Percentage of evaluation completed.
    /// </summary>
    public decimal ProgressPercentage => TotalBidders > 0
        ? Math.Round((decimal)BiddersScored / TotalBidders * 100, 1)
        : 0;

    /// <summary>
    /// Whether the panelist has completed all scoring.
    /// </summary>
    public bool IsComplete => BiddersScored == TotalBidders && TotalBidders > 0;
}
