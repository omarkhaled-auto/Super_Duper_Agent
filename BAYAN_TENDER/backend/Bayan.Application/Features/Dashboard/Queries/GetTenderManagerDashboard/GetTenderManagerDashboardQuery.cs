using Bayan.Application.Features.Dashboard.DTOs;
using MediatR;

namespace Bayan.Application.Features.Dashboard.Queries.GetTenderManagerDashboard;

/// <summary>
/// Query for retrieving the Tender Manager dashboard data.
/// </summary>
public class GetTenderManagerDashboardQuery : IRequest<TenderManagerDashboardDto>
{
    /// <summary>
    /// Number of days to look ahead for deadlines (default: 7).
    /// </summary>
    public int DeadlineDaysAhead { get; set; } = 7;

    /// <summary>
    /// Maximum number of recent activities to return (default: 10).
    /// </summary>
    public int ActivityLimit { get; set; } = 10;

    /// <summary>
    /// Maximum number of active tenders to return (default: 5).
    /// </summary>
    public int ActiveTendersLimit { get; set; } = 5;
}
