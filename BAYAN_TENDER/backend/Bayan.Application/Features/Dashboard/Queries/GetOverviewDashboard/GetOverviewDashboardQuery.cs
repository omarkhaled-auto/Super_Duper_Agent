using Bayan.Application.Features.Dashboard.DTOs;
using MediatR;

namespace Bayan.Application.Features.Dashboard.Queries.GetOverviewDashboard;

/// <summary>
/// Query for retrieving the overview dashboard data.
/// </summary>
public class GetOverviewDashboardQuery : IRequest<OverviewDashboardDto>
{
    /// <summary>
    /// Number of months to look back for the monthly trend (default: 6).
    /// </summary>
    public int MonthsBack { get; set; } = 6;
}
