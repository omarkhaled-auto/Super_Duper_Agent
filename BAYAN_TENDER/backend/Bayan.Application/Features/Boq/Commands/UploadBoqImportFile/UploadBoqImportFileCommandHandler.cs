using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Application.Features.Boq.Services;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Boq.Commands.UploadBoqImportFile;

/// <summary>
/// Handler for UploadBoqImportFileCommand.
/// </summary>
public class UploadBoqImportFileCommandHandler : IRequestHandler<UploadBoqImportFileCommand, ExcelPreviewDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IExcelService _excelService;
    private readonly IBoqImportSessionService _sessionService;
    private readonly IBoqColumnMappingService _mappingService;
    private readonly ILogger<UploadBoqImportFileCommandHandler> _logger;

    private const int PreviewRowCount = 10;

    public UploadBoqImportFileCommandHandler(
        IApplicationDbContext context,
        IExcelService excelService,
        IBoqImportSessionService sessionService,
        IBoqColumnMappingService mappingService,
        ILogger<UploadBoqImportFileCommandHandler> logger)
    {
        _context = context;
        _excelService = excelService;
        _sessionService = sessionService;
        _mappingService = mappingService;
        _logger = logger;
    }

    public async Task<ExcelPreviewDto> Handle(
        UploadBoqImportFileCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists
        var tenderExists = await _context.Tenders
            .AnyAsync(t => t.Id == request.TenderId, cancellationToken);

        if (!tenderExists)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        _logger.LogInformation(
            "Processing BOQ import file '{FileName}' ({FileSize} bytes) for tender {TenderId}",
            request.FileName,
            request.FileSize,
            request.TenderId);

        // Parse the Excel file
        var parseResult = await _excelService.ParseExcelFileAsync(request.FileStream, cancellationToken);

        if (!parseResult.Success)
        {
            throw new ApplicationException($"Failed to parse Excel file: {parseResult.ErrorMessage}");
        }

        if (parseResult.Sheets.Count == 0 || parseResult.Headers.Count == 0)
        {
            throw new ApplicationException("Excel file contains no data or headers could not be detected.");
        }

        var firstSheet = parseResult.Sheets[0];

        // Get suggested column mappings
        var suggestedMappings = _mappingService.SuggestMappings(firstSheet.Headers);

        // Create import session
        var sessionId = await _sessionService.CreateSessionAsync(
            request.TenderId,
            request.FileName,
            request.FileSize,
            parseResult,
            suggestedMappings,
            cancellationToken);

        // Build preview response
        var columns = BuildColumnInfo(firstSheet);
        var previewRows = firstSheet.Rows.Take(PreviewRowCount).ToList();

        var preview = new ExcelPreviewDto
        {
            ImportSessionId = sessionId,
            FileName = request.FileName,
            FileSizeBytes = request.FileSize,
            Columns = columns,
            PreviewRows = previewRows,
            TotalRowCount = firstSheet.Rows.Count,
            HeaderRowIndex = firstSheet.HeaderRowIndex,
            SheetName = firstSheet.Name,
            AvailableSheets = parseResult.Sheets.Select(s => s.Name).ToList(),
            SuggestedMappings = suggestedMappings
        };

        _logger.LogInformation(
            "Created BOQ import session {SessionId} with {RowCount} rows, {ColumnCount} columns, {MappingCount} suggested mappings",
            sessionId,
            firstSheet.Rows.Count,
            firstSheet.Headers.Count,
            suggestedMappings.Count);

        return preview;
    }

    private static List<ExcelColumnDto> BuildColumnInfo(ExcelSheetData sheet)
    {
        var columns = new List<ExcelColumnDto>();

        for (var i = 0; i < sheet.Headers.Count; i++)
        {
            var header = sheet.Headers[i];
            var colIndex = i;

            // Get sample values from the column
            var sampleValues = sheet.Rows
                .Take(5)
                .Select(row => row.TryGetValue(header, out var value) ? value?.ToString() ?? string.Empty : string.Empty)
                .Where(v => !string.IsNullOrWhiteSpace(v))
                .Take(5)
                .ToList();

            // Calculate fill rate
            var nonEmptyCount = sheet.Rows
                .Count(row => row.TryGetValue(header, out var value) && value != null && !string.IsNullOrWhiteSpace(value.ToString()));
            var fillRate = sheet.Rows.Count > 0 ? (double)nonEmptyCount / sheet.Rows.Count * 100 : 0;

            // Detect data type
            var dataType = DetectColumnDataType(sheet.Rows, header);

            columns.Add(new ExcelColumnDto
            {
                Index = colIndex,
                Header = header,
                SampleValues = sampleValues,
                DataType = dataType,
                FillRate = Math.Round(fillRate, 1)
            });
        }

        return columns;
    }

    private static string DetectColumnDataType(List<Dictionary<string, object?>> rows, string header)
    {
        var values = rows
            .Take(20)
            .Select(row => row.TryGetValue(header, out var value) ? value : null)
            .Where(v => v != null)
            .ToList();

        if (values.Count == 0)
        {
            return "string";
        }

        // Check if all values are numeric
        if (values.All(v => v is double or float or decimal or int or long ||
            (v is string s && decimal.TryParse(s, out _))))
        {
            return "number";
        }

        // Check if all values are dates
        if (values.All(v => v is DateTime ||
            (v is string s && DateTime.TryParse(s, out _))))
        {
            return "date";
        }

        return "string";
    }
}
