using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Commands.CalculateCombinedScores;

/// <summary>
/// Command to calculate combined scores for all bidders in a tender.
/// Formula: (TechWeight/100 * TechScore) + (CommWeight/100 * CommScore)
/// </summary>
public class CalculateCombinedScoresCommand : IRequest<CombinedScorecardDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Technical weight percentage (optional, defaults to tender settings).
    /// </summary>
    public int? TechnicalWeight { get; set; }

    /// <summary>
    /// Commercial weight percentage (optional, defaults to tender settings).
    /// </summary>
    public int? CommercialWeight { get; set; }

    public CalculateCombinedScoresCommand()
    {
    }

    public CalculateCombinedScoresCommand(Guid tenderId, int? technicalWeight = null, int? commercialWeight = null)
    {
        TenderId = tenderId;
        TechnicalWeight = technicalWeight;
        CommercialWeight = commercialWeight;
    }
}
