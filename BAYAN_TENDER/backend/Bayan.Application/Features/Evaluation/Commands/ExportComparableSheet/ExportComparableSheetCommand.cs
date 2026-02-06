using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Commands.ExportComparableSheet;

/// <summary>
/// Command to export the comparable sheet to Excel.
/// </summary>
public class ExportComparableSheetCommand : IRequest<ExportComparableSheetResultDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Whether to include provisional sums.
    /// </summary>
    public bool IncludeProvisionalSums { get; set; } = true;

    /// <summary>
    /// Whether to include alternates.
    /// </summary>
    public bool IncludeAlternates { get; set; } = true;

    /// <summary>
    /// Whether to include daywork items.
    /// </summary>
    public bool IncludeDaywork { get; set; } = true;

    public ExportComparableSheetCommand()
    {
    }

    public ExportComparableSheetCommand(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
