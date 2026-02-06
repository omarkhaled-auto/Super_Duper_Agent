using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Commands.UpdateOutlierStatus;

/// <summary>
/// Command to recalculate outlier status for all bid pricing in a tender.
/// </summary>
public class UpdateOutlierStatusCommand : IRequest<OutlierRecalculationResultDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// High threshold percentage (>20% deviation = High severity).
    /// </summary>
    public decimal HighThreshold { get; set; } = 20m;

    /// <summary>
    /// Medium threshold percentage (>10% deviation = Medium severity).
    /// </summary>
    public decimal MediumThreshold { get; set; } = 10m;

    public UpdateOutlierStatusCommand()
    {
    }

    public UpdateOutlierStatusCommand(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
