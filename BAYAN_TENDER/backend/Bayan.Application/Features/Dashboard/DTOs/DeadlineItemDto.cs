namespace Bayan.Application.Features.Dashboard.DTOs;

/// <summary>
/// Data transfer object for an upcoming deadline item.
/// </summary>
public class DeadlineItemDto
{
    /// <summary>
    /// Tender ID.
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
    /// Type of deadline (e.g., "Submission", "Clarification", "Opening").
    /// </summary>
    public string DeadlineType { get; set; } = string.Empty;

    /// <summary>
    /// The deadline date and time.
    /// </summary>
    public DateTime Deadline { get; set; }

    /// <summary>
    /// Days remaining until the deadline (negative if overdue).
    /// </summary>
    public int DaysRemaining => (int)(Deadline - DateTime.UtcNow).TotalDays;

    /// <summary>
    /// Hours remaining until the deadline.
    /// </summary>
    public int HoursRemaining => (int)(Deadline - DateTime.UtcNow).TotalHours;

    /// <summary>
    /// Whether the deadline is overdue.
    /// </summary>
    public bool IsOverdue => Deadline < DateTime.UtcNow;

    /// <summary>
    /// Whether the deadline is approaching (within 48 hours).
    /// </summary>
    public bool IsUrgent => !IsOverdue && HoursRemaining <= 48;
}
