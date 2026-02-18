using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetAvailablePanelists;

/// <summary>
/// Query to get active internal users who can be assigned as panelists for a tender.
/// Excludes Bidder-role users and already-assigned panelists.
/// </summary>
public class GetAvailablePanelistsQuery : IRequest<List<PanelistDto>>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    public GetAvailablePanelistsQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
