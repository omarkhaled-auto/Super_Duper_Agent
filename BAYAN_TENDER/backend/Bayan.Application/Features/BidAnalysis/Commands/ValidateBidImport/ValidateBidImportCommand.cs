using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;

namespace Bayan.Application.Features.BidAnalysis.Commands.ValidateBidImport;

/// <summary>
/// Command to validate a bid submission before import.
/// Performs formula checks, data validation, coverage analysis, and outlier detection.
/// </summary>
public record ValidateBidImportCommand : IRequest<ValidationResultDto>
{
    /// <summary>
    /// Tender identifier.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// Bid submission identifier.
    /// </summary>
    public Guid BidSubmissionId { get; init; }

    /// <summary>
    /// Tolerance percentage for formula validation (Amount = Qty x Rate).
    /// Default is 1% tolerance.
    /// </summary>
    public decimal FormulaTolerancePercent { get; init; } = 1.0m;

    /// <summary>
    /// Whether to perform outlier detection against other imported bids.
    /// </summary>
    public bool DetectOutliers { get; init; } = true;

    /// <summary>
    /// Threshold percentage for outlier detection.
    /// Items with deviation above this threshold are flagged.
    /// </summary>
    public decimal OutlierThresholdPercent { get; init; } = 30.0m;
}
