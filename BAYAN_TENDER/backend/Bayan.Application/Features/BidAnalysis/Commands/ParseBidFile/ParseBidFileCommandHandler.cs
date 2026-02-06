using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.BidAnalysis.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.BidAnalysis.Commands.ParseBidFile;

/// <summary>
/// Handler for ParseBidFileCommand.
/// </summary>
public class ParseBidFileCommandHandler : IRequestHandler<ParseBidFileCommand, ParseBidResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IFileStorageService _fileStorage;
    private readonly IExcelService _excelService;
    private readonly ILogger<ParseBidFileCommandHandler> _logger;

    // Common column header patterns for auto-detection
    private static readonly Dictionary<string, string[]> ColumnPatterns = new(StringComparer.OrdinalIgnoreCase)
    {
        { "ItemNumber", new[] { "item no", "item number", "item #", "no.", "no", "item", "s.no", "s.n", "sl.no", "sl no", "serial" } },
        { "Description", new[] { "description", "desc", "item description", "work description", "particulars", "name" } },
        { "Quantity", new[] { "quantity", "qty", "qty.", "amount", "vol", "volume" } },
        { "Uom", new[] { "uom", "unit", "unit of measurement", "u.o.m", "units", "measure" } },
        { "UnitRate", new[] { "rate", "unit rate", "unit price", "price", "rate/unit", "unit cost" } },
        { "Amount", new[] { "total", "total amount", "amount", "total price", "value", "total cost", "extended amount" } },
        { "Currency", new[] { "currency", "curr", "ccy" } }
    };

    public ParseBidFileCommandHandler(
        IApplicationDbContext context,
        IFileStorageService fileStorage,
        IExcelService excelService,
        ILogger<ParseBidFileCommandHandler> logger)
    {
        _context = context;
        _fileStorage = fileStorage;
        _excelService = excelService;
        _logger = logger;
    }

    public async Task<ParseBidResultDto> Handle(ParseBidFileCommand request, CancellationToken cancellationToken)
    {
        // Get bid submission
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == request.BidId && b.TenderId == request.TenderId, cancellationToken);

        if (bid == null)
        {
            throw new NotFoundException("BidSubmission", request.BidId);
        }

        if (string.IsNullOrEmpty(bid.OriginalFilePath))
        {
            return new ParseBidResultDto
            {
                Success = false,
                ErrorMessage = "No file has been uploaded for this bid submission."
            };
        }

        // Update status to parsing
        bid.ImportStatus = BidImportStatus.Parsing;
        bid.ImportStartedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync(cancellationToken);

        try
        {
            // Download and parse the file
            using var fileStream = await _fileStorage.DownloadFileAsync(bid.OriginalFilePath, cancellationToken);
            var parseResult = await _excelService.ParseExcelFileAsync(fileStream, cancellationToken);

            if (!parseResult.Success)
            {
                bid.ImportStatus = BidImportStatus.Failed;
                await _context.SaveChangesAsync(cancellationToken);

                return new ParseBidResultDto
                {
                    Success = false,
                    ErrorMessage = parseResult.ErrorMessage ?? "Failed to parse the Excel file."
                };
            }

            var result = new ParseBidResultDto
            {
                Success = true,
                Sheets = parseResult.Sheets.Select(s => new SheetInfoDto
                {
                    Name = s.Name,
                    Index = s.Index,
                    RowCount = s.TotalRows,
                    ColumnCount = s.TotalColumns
                }).ToList()
            };

            // Use the first sheet by default
            var primarySheet = parseResult.Sheets.FirstOrDefault();
            if (primarySheet != null)
            {
                result.HeaderRowIndex = primarySheet.HeaderRowIndex;
                result.ItemCount = primarySheet.Rows.Count;

                // Build column info
                result.Columns = primarySheet.Headers.Select((header, index) => new ColumnInfoDto
                {
                    Index = index,
                    Letter = GetColumnLetter(index),
                    Header = header,
                    DataType = DetectDataType(primarySheet.Rows, header),
                    SampleValues = GetSampleValues(primarySheet.Rows, header, 5),
                    SuggestedMapping = SuggestMapping(header)
                }).ToList();

                // Get preview rows
                result.PreviewRows = primarySheet.Rows.Take(request.PreviewRowCount).ToList();

                // Build suggested mappings
                result.SuggestedMappings = BuildSuggestedMappings(result.Columns);
            }

            // Update status to parsed
            bid.ImportStatus = BidImportStatus.Parsed;
            await _context.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "Successfully parsed bid file for bid {BidId}. Found {SheetCount} sheets, {ItemCount} items.",
                request.BidId, result.Sheets.Count, result.ItemCount);

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing bid file for bid {BidId}", request.BidId);

            bid.ImportStatus = BidImportStatus.Failed;
            await _context.SaveChangesAsync(cancellationToken);

            return new ParseBidResultDto
            {
                Success = false,
                ErrorMessage = $"Error parsing file: {ex.Message}"
            };
        }
    }

    private static string GetColumnLetter(int columnIndex)
    {
        var letter = string.Empty;
        while (columnIndex >= 0)
        {
            letter = (char)('A' + columnIndex % 26) + letter;
            columnIndex = columnIndex / 26 - 1;
        }
        return letter;
    }

    private static string DetectDataType(List<Dictionary<string, object?>> rows, string header)
    {
        var values = rows
            .Take(20)
            .Select(r => r.GetValueOrDefault(header))
            .Where(v => v != null)
            .ToList();

        if (values.Count == 0) return "string";

        var numericCount = values.Count(v => decimal.TryParse(v?.ToString(), out _));
        var dateCount = values.Count(v => DateTime.TryParse(v?.ToString(), out _));

        if (numericCount > values.Count * 0.8) return "number";
        if (dateCount > values.Count * 0.8) return "date";
        return "string";
    }

    private static List<string> GetSampleValues(List<Dictionary<string, object?>> rows, string header, int count)
    {
        return rows
            .Take(count)
            .Select(r => r.GetValueOrDefault(header)?.ToString() ?? string.Empty)
            .Where(v => !string.IsNullOrWhiteSpace(v))
            .Take(count)
            .ToList();
    }

    private static string? SuggestMapping(string header)
    {
        var normalizedHeader = header.ToLowerInvariant().Trim();

        foreach (var (field, patterns) in ColumnPatterns)
        {
            if (patterns.Any(p => normalizedHeader.Contains(p, StringComparison.OrdinalIgnoreCase) ||
                                  p.Contains(normalizedHeader, StringComparison.OrdinalIgnoreCase)))
            {
                return field;
            }
        }

        return null;
    }

    private static ColumnMappingsDto BuildSuggestedMappings(List<ColumnInfoDto> columns)
    {
        var mappings = new ColumnMappingsDto();

        foreach (var column in columns)
        {
            switch (column.SuggestedMapping)
            {
                case "ItemNumber" when mappings.ItemNumberColumn == null:
                    mappings.ItemNumberColumn = column.Header;
                    break;
                case "Description" when mappings.DescriptionColumn == null:
                    mappings.DescriptionColumn = column.Header;
                    break;
                case "Quantity" when mappings.QuantityColumn == null:
                    mappings.QuantityColumn = column.Header;
                    break;
                case "Uom" when mappings.UomColumn == null:
                    mappings.UomColumn = column.Header;
                    break;
                case "UnitRate" when mappings.UnitRateColumn == null:
                    mappings.UnitRateColumn = column.Header;
                    break;
                case "Amount" when mappings.AmountColumn == null:
                    mappings.AmountColumn = column.Header;
                    break;
                case "Currency" when mappings.CurrencyColumn == null:
                    mappings.CurrencyColumn = column.Header;
                    break;
            }
        }

        return mappings;
    }
}
