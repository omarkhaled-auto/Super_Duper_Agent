using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelistAssignments;

/// <summary>
/// Query to get the current panelist's assignments for a tender.
/// Returns bidders to score and progress information.
/// </summary>
public class GetPanelistAssignmentsQuery : IRequest<PanelistAssignmentDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    public GetPanelistAssignmentsQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
