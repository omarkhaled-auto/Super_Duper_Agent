using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Commands.CalculateCommercialScores;

/// <summary>
/// Command to calculate commercial scores for all bidders in a tender.
/// Formula: (Lowest Total / This Total) x 100
/// </summary>
public class CalculateCommercialScoresCommand : IRequest<CalculateCommercialScoresResultDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Whether to include provisional sums in the total calculation.
    /// </summary>
    public bool IncludeProvisionalSums { get; set; } = true;

    /// <summary>
    /// Whether to include alternates in the total calculation.
    /// </summary>
    public bool IncludeAlternates { get; set; } = true;

    public CalculateCommercialScoresCommand()
    {
    }

    public CalculateCommercialScoresCommand(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
