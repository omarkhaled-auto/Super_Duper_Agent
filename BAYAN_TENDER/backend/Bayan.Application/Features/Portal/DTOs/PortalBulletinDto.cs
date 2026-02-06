namespace Bayan.Application.Features.Portal.DTOs;

/// <summary>
/// Data transfer object for clarification bulletins displayed in the bidder portal.
/// </summary>
public class PortalBulletinDto
{
    /// <summary>
    /// Bulletin unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Bulletin number (sequential within tender).
    /// </summary>
    public int BulletinNumber { get; set; }

    /// <summary>
    /// Date the bulletin was issued.
    /// </summary>
    public DateTime IssueDate { get; set; }

    /// <summary>
    /// Introduction text for the bulletin.
    /// </summary>
    public string? Introduction { get; set; }

    /// <summary>
    /// Closing notes for the bulletin.
    /// </summary>
    public string? ClosingNotes { get; set; }

    /// <summary>
    /// Whether PDF is available for download.
    /// </summary>
    public bool HasPdf { get; set; }

    /// <summary>
    /// When the bulletin was published.
    /// </summary>
    public DateTime PublishedAt { get; set; }

    /// <summary>
    /// Number of clarifications included in this bulletin.
    /// </summary>
    public int ClarificationCount { get; set; }
}
