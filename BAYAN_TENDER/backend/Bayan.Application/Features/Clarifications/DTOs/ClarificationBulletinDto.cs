namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for clarification bulletin summary information.
/// </summary>
public class ClarificationBulletinDto
{
    /// <summary>
    /// Unique identifier of the bulletin.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// ID of the tender this bulletin belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bulletin number (sequential within tender).
    /// </summary>
    public int BulletinNumber { get; set; }

    /// <summary>
    /// Formatted bulletin number (e.g., QB-001).
    /// </summary>
    public string BulletinNumberFormatted => $"QB-{BulletinNumber:D3}";

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
    /// Path to generated PDF in storage.
    /// </summary>
    public string? PdfPath { get; set; }

    /// <summary>
    /// ID of user who published the bulletin.
    /// </summary>
    public Guid PublishedBy { get; set; }

    /// <summary>
    /// Name of user who published the bulletin.
    /// </summary>
    public string PublishedByName { get; set; } = string.Empty;

    /// <summary>
    /// When the bulletin was published.
    /// </summary>
    public DateTime PublishedAt { get; set; }

    /// <summary>
    /// Number of questions included in this bulletin.
    /// </summary>
    public int QuestionCount { get; set; }

    /// <summary>
    /// List of clarifications included in this bulletin.
    /// </summary>
    public List<ClarificationBulletinQuestionDto> Questions { get; set; } = new();
}

/// <summary>
/// Data transfer object for a question within a clarification bulletin.
/// </summary>
public class ClarificationBulletinQuestionDto
{
    /// <summary>
    /// Unique identifier of the clarification.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Reference number (e.g., CL-001).
    /// </summary>
    public string ReferenceNumber { get; set; } = string.Empty;

    /// <summary>
    /// Subject of the clarification.
    /// </summary>
    public string Subject { get; set; } = string.Empty;

    /// <summary>
    /// The question being asked.
    /// </summary>
    public string Question { get; set; } = string.Empty;

    /// <summary>
    /// The answer to the question.
    /// </summary>
    public string Answer { get; set; } = string.Empty;

    /// <summary>
    /// Related BOQ section reference.
    /// </summary>
    public string? RelatedBoqSection { get; set; }

    /// <summary>
    /// When the question was answered.
    /// </summary>
    public DateTime? AnsweredAt { get; set; }
}
