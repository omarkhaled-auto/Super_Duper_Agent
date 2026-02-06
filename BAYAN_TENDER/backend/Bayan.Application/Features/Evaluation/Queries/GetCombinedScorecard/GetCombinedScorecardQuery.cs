using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Queries.GetCombinedScorecard;

/// <summary>
/// Query to get the combined scorecard for a tender.
/// </summary>
public class GetCombinedScorecardQuery : IRequest<CombinedScorecardDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Technical weight percentage (optional, uses stored values if not provided).
    /// </summary>
    public int? TechnicalWeight { get; set; }

    /// <summary>
    /// Commercial weight percentage (optional, uses stored values if not provided).
    /// </summary>
    public int? CommercialWeight { get; set; }

    public GetCombinedScorecardQuery()
    {
    }

    public GetCombinedScorecardQuery(Guid tenderId, int? technicalWeight = null, int? commercialWeight = null)
    {
        TenderId = tenderId;
        TechnicalWeight = technicalWeight;
        CommercialWeight = commercialWeight;
    }
}
