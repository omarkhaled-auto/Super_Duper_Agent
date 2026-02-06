using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetTechnicalScoresSummary;

/// <summary>
/// Query to get the technical scores summary with matrix view, averages, variance, and ranks.
/// </summary>
public class GetTechnicalScoresSummaryQuery : IRequest<TechnicalScoresSummaryDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    public GetTechnicalScoresSummaryQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
