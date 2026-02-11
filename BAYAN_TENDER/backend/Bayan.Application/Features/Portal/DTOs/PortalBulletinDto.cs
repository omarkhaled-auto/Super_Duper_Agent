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

    /// <summary>
    /// The published Q&A items in this bulletin.
    /// </summary>
    public List<PortalBulletinClarificationDto> Clarifications { get; set; } = new();
}

/// <summary>
/// A single Q&A item within a published bulletin (portal-facing).
/// </summary>
public class PortalBulletinClarificationDto
{
    public Guid Id { get; set; }
    public string ReferenceNumber { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string Question { get; set; } = string.Empty;
    public string Answer { get; set; } = string.Empty;
    public string? RelatedBoqSection { get; set; }
    public DateTime? AnsweredAt { get; set; }

    /// <summary>
    /// File attachments associated with this clarification.
    /// </summary>
    public List<PortalAttachmentDto> Attachments { get; set; } = new();
}

/// <summary>
/// Lightweight attachment info for portal display (no internal file paths).
/// </summary>
public class PortalAttachmentDto
{
    public Guid Id { get; set; }
    public string FileName { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public string ContentType { get; set; } = string.Empty;
}
