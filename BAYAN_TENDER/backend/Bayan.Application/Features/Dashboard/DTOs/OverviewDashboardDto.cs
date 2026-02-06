namespace Bayan.Application.Features.Dashboard.DTOs;

/// <summary>
/// Data transfer object for the overview dashboard.
/// </summary>
public class OverviewDashboardDto
{
    /// <summary>
    /// Tender counts grouped by status.
    /// </summary>
    public TenderCountsByStatusDto TenderCounts { get; set; } = new();

    /// <summary>
    /// Total number of registered bidders.
    /// </summary>
    public int TotalBidders { get; set; }

    /// <summary>
    /// Number of active bidders.
    /// </summary>
    public int ActiveBidders { get; set; }

    /// <summary>
    /// Number of approval workflows currently in progress.
    /// </summary>
    public int PendingApprovals { get; set; }

    /// <summary>
    /// Total contract value of awarded tenders.
    /// </summary>
    public decimal TotalContractValue { get; set; }

    /// <summary>
    /// Currency code for the total contract value.
    /// </summary>
    public string Currency { get; set; } = "SAR";

    /// <summary>
    /// Monthly trend data for the specified period.
    /// </summary>
    public List<MonthlyTrendItemDto> MonthlyTrend { get; set; } = new();
}

/// <summary>
/// Tender counts grouped by status.
/// </summary>
public class TenderCountsByStatusDto
{
    /// <summary>
    /// Number of tenders in Draft status.
    /// </summary>
    public int Draft { get; set; }

    /// <summary>
    /// Number of tenders in Active status.
    /// </summary>
    public int Active { get; set; }

    /// <summary>
    /// Number of tenders in Evaluation status.
    /// </summary>
    public int Evaluation { get; set; }

    /// <summary>
    /// Number of tenders in Awarded status.
    /// </summary>
    public int Awarded { get; set; }

    /// <summary>
    /// Number of tenders in Cancelled status.
    /// </summary>
    public int Cancelled { get; set; }

    /// <summary>
    /// Total number of tenders across all statuses.
    /// </summary>
    public int Total { get; set; }
}

/// <summary>
/// A single month's trend data for the overview dashboard.
/// </summary>
public class MonthlyTrendItemDto
{
    /// <summary>
    /// Month label (e.g. "2025-01").
    /// </summary>
    public string Month { get; set; } = string.Empty;

    /// <summary>
    /// Number of tenders created in this month.
    /// </summary>
    public int TendersCreated { get; set; }

    /// <summary>
    /// Number of bids received in this month.
    /// </summary>
    public int BidsReceived { get; set; }

    /// <summary>
    /// Total contract value of tenders awarded in this month.
    /// </summary>
    public decimal ContractValue { get; set; }
}
