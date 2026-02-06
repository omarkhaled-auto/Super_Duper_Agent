using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Dashboard.DTOs;

/// <summary>
/// Data transfer object for the Tender Manager dashboard.
/// </summary>
public class TenderManagerDashboardDto
{
    /// <summary>
    /// KPI metrics for the dashboard.
    /// </summary>
    public List<DashboardKpiDto> Kpis { get; set; } = new();

    /// <summary>
    /// Recent active tenders (limited to 5).
    /// </summary>
    public List<ActiveTenderDto> ActiveTenders { get; set; } = new();

    /// <summary>
    /// Upcoming deadlines within the next 7 days.
    /// </summary>
    public List<DeadlineItemDto> UpcomingDeadlines { get; set; } = new();

    /// <summary>
    /// Recent activity feed (limited to 10).
    /// </summary>
    public List<ActivityFeedItemDto> RecentActivity { get; set; } = new();
}

/// <summary>
/// Data transfer object for an active tender in the dashboard.
/// </summary>
public class ActiveTenderDto
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Tender reference number.
    /// </summary>
    public string Reference { get; set; } = string.Empty;

    /// <summary>
    /// Tender title.
    /// </summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Client name.
    /// </summary>
    public string ClientName { get; set; } = string.Empty;

    /// <summary>
    /// Current status.
    /// </summary>
    public TenderStatus Status { get; set; }

    /// <summary>
    /// Human-readable status text.
    /// </summary>
    public string StatusText => Status switch
    {
        TenderStatus.Draft => "Draft",
        TenderStatus.Active => "Active",
        TenderStatus.Evaluation => "Evaluation",
        TenderStatus.Awarded => "Awarded",
        TenderStatus.Cancelled => "Cancelled",
        _ => "Unknown"
    };

    /// <summary>
    /// Submission deadline.
    /// </summary>
    public DateTime SubmissionDeadline { get; set; }

    /// <summary>
    /// Number of bids received.
    /// </summary>
    public int BidsReceived { get; set; }

    /// <summary>
    /// Number of invited bidders.
    /// </summary>
    public int InvitedBidders { get; set; }

    /// <summary>
    /// Days remaining until deadline.
    /// </summary>
    public int DaysRemaining => (int)(SubmissionDeadline - DateTime.UtcNow).TotalDays;

    /// <summary>
    /// When the tender was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }
}
