using Bayan.Application.Features.Evaluation.DTOs;

namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for exporting comparable sheet to Excel.
/// </summary>
public interface IComparableSheetExportService
{
    /// <summary>
    /// Exports the comparable sheet to an Excel file.
    /// </summary>
    /// <param name="comparableSheet">The comparable sheet data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The export result containing the file content.</returns>
    Task<ExportComparableSheetResultDto> ExportToExcelAsync(
        ComparableSheetDto comparableSheet,
        CancellationToken cancellationToken = default);
}
