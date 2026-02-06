using Bayan.Application.Features.Dashboard.DTOs;
using MediatR;

namespace Bayan.Application.Features.Dashboard.Queries.GetApproverDashboard;

/// <summary>
/// Query for retrieving the Approver dashboard data.
/// </summary>
public class GetApproverDashboardQuery : IRequest<ApproverDashboardDto>
{
    /// <summary>
    /// Maximum number of recent decisions to return (default: 10).
    /// </summary>
    public int RecentDecisionsLimit { get; set; } = 10;
}
