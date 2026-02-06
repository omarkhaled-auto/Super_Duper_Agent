using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelistScores;

/// <summary>
/// Query to get the current panelist's scores for a specific bidder.
/// </summary>
public class GetPanelistScoresQuery : IRequest<List<TechnicalScoreDto>>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    /// <summary>
    /// The bidder's unique identifier.
    /// </summary>
    public Guid BidderId { get; }

    public GetPanelistScoresQuery(Guid tenderId, Guid bidderId)
    {
        TenderId = tenderId;
        BidderId = bidderId;
    }
}
