using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Application.Features.Evaluation.Queries.GetComparableSheet;
using MediatR;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Commands.ExportComparableSheet;

/// <summary>
/// Handler for ExportComparableSheetCommand.
/// </summary>
public class ExportComparableSheetCommandHandler : IRequestHandler<ExportComparableSheetCommand, ExportComparableSheetResultDto>
{
    private readonly IMediator _mediator;
    private readonly IComparableSheetExportService _exportService;
    private readonly ILogger<ExportComparableSheetCommandHandler> _logger;

    public ExportComparableSheetCommandHandler(
        IMediator mediator,
        IComparableSheetExportService exportService,
        ILogger<ExportComparableSheetCommandHandler> logger)
    {
        _mediator = mediator;
        _exportService = exportService;
        _logger = logger;
    }

    public async Task<ExportComparableSheetResultDto> Handle(
        ExportComparableSheetCommand request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Exporting comparable sheet to Excel for tender {TenderId}", request.TenderId);

        // Get the comparable sheet data
        var query = new GetComparableSheetQuery
        {
            TenderId = request.TenderId,
            IncludeProvisionalSums = request.IncludeProvisionalSums,
            IncludeAlternates = request.IncludeAlternates,
            IncludeDaywork = request.IncludeDaywork
        };

        var comparableSheet = await _mediator.Send(query, cancellationToken);

        // Export to Excel
        var result = await _exportService.ExportToExcelAsync(comparableSheet, cancellationToken);

        _logger.LogInformation(
            "Comparable sheet exported successfully for tender {TenderId}: {FileSize} bytes",
            request.TenderId, result.FileContent.Length);

        return result;
    }
}
