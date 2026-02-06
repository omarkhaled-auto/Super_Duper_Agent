using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.BidAnalysis.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.BidAnalysis.Commands.MapBidColumns;

/// <summary>
/// Handler for MapBidColumnsCommand.
/// </summary>
public class MapBidColumnsCommandHandler : IRequestHandler<MapBidColumnsCommand, ImportBidDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IFileStorageService _fileStorage;
    private readonly IExcelService _excelService;
    private readonly ILogger<MapBidColumnsCommandHandler> _logger;

    public MapBidColumnsCommandHandler(
        IApplicationDbContext context,
        IFileStorageService fileStorage,
        IExcelService excelService,
        ILogger<MapBidColumnsCommandHandler> logger)
    {
        _context = context;
        _fileStorage = fileStorage;
        _excelService = excelService;
        _logger = logger;
    }

    public async Task<ImportBidDto> Handle(MapBidColumnsCommand request, CancellationToken cancellationToken)
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
            throw new InvalidOperationException("No file has been uploaded for this bid submission.");
        }

        if (bid.ImportStatus != BidImportStatus.Parsed)
        {
            throw new InvalidOperationException($"Bid must be in 'Parsed' status to map columns. Current status: {bid.ImportStatus}");
        }

        // Update status to mapping
        bid.ImportStatus = BidImportStatus.Mapping;
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
                throw new InvalidOperationException(parseResult.ErrorMessage ?? "Failed to parse the Excel file.");
            }

            // Get the target sheet
            var mappings = request.ColumnMappings;
            var sheet = !string.IsNullOrEmpty(mappings.SheetName)
                ? parseResult.Sheets.FirstOrDefault(s => s.Name.Equals(mappings.SheetName, StringComparison.OrdinalIgnoreCase))
                : parseResult.Sheets.ElementAtOrDefault(mappings.SheetIndex);

            sheet ??= parseResult.Sheets.FirstOrDefault();

            if (sheet == null)
            {
                bid.ImportStatus = BidImportStatus.Failed;
                await _context.SaveChangesAsync(cancellationToken);
                throw new InvalidOperationException("No valid sheet found in the file.");
            }

            // Extract items using the mappings
            var items = new List<ImportBidItemDto>();
            var startRow = mappings.StartRowIndex;

            for (var i = startRow; i < sheet.Rows.Count; i++)
            {
                var row = sheet.Rows[i];
                var item = ExtractBidItem(row, mappings, i);

                // Skip completely empty rows
                if (IsEmptyItem(item))
                {
                    continue;
                }

                items.Add(item);
            }

            var result = new ImportBidDto
            {
                ColumnMappings = mappings,
                Items = items
            };

            // Update status to mapped
            bid.ImportStatus = BidImportStatus.Mapped;
            await _context.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "Successfully mapped {ItemCount} items from bid file for bid {BidId}.",
                items.Count, request.BidId);

            return result;
        }
        catch (Exception ex) when (ex is not NotFoundException && ex is not InvalidOperationException)
        {
            _logger.LogError(ex, "Error mapping columns for bid {BidId}", request.BidId);

            bid.ImportStatus = BidImportStatus.Failed;
            await _context.SaveChangesAsync(cancellationToken);

            throw new InvalidOperationException($"Error mapping columns: {ex.Message}", ex);
        }
    }

    private static ImportBidItemDto ExtractBidItem(Dictionary<string, object?> row, ColumnMappingsDto mappings, int rowIndex)
    {
        var item = new ImportBidItemDto
        {
            RowIndex = rowIndex,
            RawValues = new Dictionary<string, object?>(row)
        };

        // Extract item number
        if (!string.IsNullOrEmpty(mappings.ItemNumberColumn))
        {
            item.ItemNumber = GetStringValue(row, mappings.ItemNumberColumn);
        }

        // Extract description
        if (!string.IsNullOrEmpty(mappings.DescriptionColumn))
        {
            item.Description = GetStringValue(row, mappings.DescriptionColumn);
        }

        // Extract quantity
        if (!string.IsNullOrEmpty(mappings.QuantityColumn))
        {
            item.Quantity = GetDecimalValue(row, mappings.QuantityColumn);
        }

        // Extract UOM
        if (!string.IsNullOrEmpty(mappings.UomColumn))
        {
            item.Uom = GetStringValue(row, mappings.UomColumn);
        }

        // Extract unit rate
        if (!string.IsNullOrEmpty(mappings.UnitRateColumn))
        {
            item.UnitRate = GetDecimalValue(row, mappings.UnitRateColumn);
        }

        // Extract amount
        if (!string.IsNullOrEmpty(mappings.AmountColumn))
        {
            item.Amount = GetDecimalValue(row, mappings.AmountColumn);
        }

        // Extract currency or use default
        if (!string.IsNullOrEmpty(mappings.CurrencyColumn))
        {
            item.Currency = GetStringValue(row, mappings.CurrencyColumn);
        }

        if (string.IsNullOrEmpty(item.Currency))
        {
            item.Currency = mappings.DefaultCurrency;
        }

        return item;
    }

    private static string? GetStringValue(Dictionary<string, object?> row, string column)
    {
        if (row.TryGetValue(column, out var value) && value != null)
        {
            return value.ToString()?.Trim();
        }
        return null;
    }

    private static decimal? GetDecimalValue(Dictionary<string, object?> row, string column)
    {
        if (row.TryGetValue(column, out var value) && value != null)
        {
            var stringValue = value.ToString()?.Trim();
            if (!string.IsNullOrEmpty(stringValue))
            {
                // Remove common currency symbols and formatting
                stringValue = stringValue
                    .Replace("$", "")
                    .Replace("£", "")
                    .Replace("€", "")
                    .Replace("AED", "")
                    .Replace(",", "")
                    .Trim();

                if (decimal.TryParse(stringValue, out var decimalValue))
                {
                    return decimalValue;
                }
            }
        }
        return null;
    }

    private static bool IsEmptyItem(ImportBidItemDto item)
    {
        return string.IsNullOrWhiteSpace(item.ItemNumber) &&
               string.IsNullOrWhiteSpace(item.Description) &&
               !item.Quantity.HasValue &&
               !item.UnitRate.HasValue &&
               !item.Amount.HasValue;
    }
}
