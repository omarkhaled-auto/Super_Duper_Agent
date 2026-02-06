using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelists;

/// <summary>
/// Query to get all panelists assigned to a tender.
/// </summary>
public class GetPanelistsQuery : IRequest<List<PanelistDto>>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    public GetPanelistsQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
