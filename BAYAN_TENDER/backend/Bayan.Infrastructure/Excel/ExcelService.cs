using System.Data;
using System.Text.RegularExpressions;
using Bayan.Application.Common.Interfaces;
using ExcelDataReader;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Excel;

/// <summary>
/// Service for parsing Excel files using ExcelDataReader.
/// </summary>
public class ExcelService : IExcelService
{
    private readonly ILogger<ExcelService> _logger;

    // Common header keywords to help detect header rows
    private static readonly string[] CommonHeaderKeywords = new[]
    {
        "item", "no", "number", "description", "quantity", "qty", "unit", "uom",
        "rate", "price", "amount", "total", "code", "ref", "specification",
        "section", "name", "material", "labor", "cost"
    };

    public ExcelService(ILogger<ExcelService> logger)
    {
        _logger = logger;

        // Required for ExcelDataReader to work with .NET Core
        System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
    }

    /// <inheritdoc />
    public async Task<ExcelParseResult> ParseExcelFileAsync(
        Stream stream,
        CancellationToken cancellationToken = default)
    {
        var result = new ExcelParseResult();

        try
        {
            // Ensure stream is at the beginning
            if (stream.CanSeek)
            {
                stream.Position = 0;
            }

            using var reader = ExcelReaderFactory.CreateReader(stream, new ExcelReaderConfiguration
            {
                FallbackEncoding = System.Text.Encoding.UTF8,
                AutodetectSeparators = new[] { ',', ';', '\t' }
            });

            var dataSet = reader.AsDataSet(new ExcelDataSetConfiguration
            {
                UseColumnDataType = false,
                ConfigureDataTable = _ => new ExcelDataTableConfiguration
                {
                    UseHeaderRow = false, // We'll detect the header row ourselves
                    EmptyColumnNamePrefix = "Column"
                }
            });

            foreach (DataTable table in dataSet.Tables)
            {
                var sheetData = await ParseSheetAsync(table, cancellationToken);
                result.Sheets.Add(sheetData);
            }

            result.Success = true;
            _logger.LogInformation("Successfully parsed Excel file with {SheetCount} sheet(s)", result.Sheets.Count);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to parse Excel file");
            result.Success = false;
            result.ErrorMessage = $"Failed to parse Excel file: {ex.Message}";
        }

        return result;
    }

    /// <inheritdoc />
    public int DetectHeaderRow(ExcelSheetData sheet)
    {
        if (sheet.RawData.Count == 0)
        {
            return 0;
        }

        var bestScore = 0;
        var bestRowIndex = 0;

        // Scan the first 20 rows to find the most likely header row
        var maxRowsToScan = Math.Min(20, sheet.RawData.Count);

        for (var rowIndex = 0; rowIndex < maxRowsToScan; rowIndex++)
        {
            var row = sheet.RawData[rowIndex];
            var score = CalculateHeaderScore(row);

            if (score > bestScore)
            {
                bestScore = score;
                bestRowIndex = rowIndex;
            }
        }

        _logger.LogDebug("Detected header row at index {RowIndex} with score {Score}", bestRowIndex, bestScore);
        return bestRowIndex;
    }

    /// <inheritdoc />
    public List<Dictionary<string, object?>> ReadDataRows(ExcelSheetData sheet, int startRow)
    {
        var rows = new List<Dictionary<string, object?>>();

        if (sheet.RawData.Count <= startRow || sheet.Headers.Count == 0)
        {
            return rows;
        }

        for (var rowIndex = startRow; rowIndex < sheet.RawData.Count; rowIndex++)
        {
            var rawRow = sheet.RawData[rowIndex];

            // Skip completely empty rows
            if (rawRow.All(cell => cell.IsEmpty))
            {
                continue;
            }

            var rowDict = new Dictionary<string, object?>();

            for (var colIndex = 0; colIndex < sheet.Headers.Count && colIndex < rawRow.Count; colIndex++)
            {
                var header = sheet.Headers[colIndex];
                if (!string.IsNullOrWhiteSpace(header))
                {
                    rowDict[header] = rawRow[colIndex].Value;
                }
            }

            rows.Add(rowDict);
        }

        return rows;
    }

    private Task<ExcelSheetData> ParseSheetAsync(DataTable table, CancellationToken cancellationToken)
    {
        var sheetData = new ExcelSheetData
        {
            Name = table.TableName,
            Index = table.ExtendedProperties.ContainsKey("Index")
                ? (int)table.ExtendedProperties["Index"]!
                : 0,
            TotalRows = table.Rows.Count,
            TotalColumns = table.Columns.Count
        };

        // Parse raw data
        for (var rowIndex = 0; rowIndex < table.Rows.Count; rowIndex++)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var row = table.Rows[rowIndex];
            var cellList = new List<ExcelCellData>();

            for (var colIndex = 0; colIndex < table.Columns.Count; colIndex++)
            {
                var value = row[colIndex];
                cellList.Add(new ExcelCellData
                {
                    Row = rowIndex,
                    Column = colIndex,
                    Value = value == DBNull.Value ? null : value,
                    IsMerged = false // ExcelDataReader doesn't provide merge info directly
                });
            }

            sheetData.RawData.Add(cellList);
        }

        // Detect header row and extract headers
        sheetData.HeaderRowIndex = DetectHeaderRow(sheetData);

        if (sheetData.RawData.Count > sheetData.HeaderRowIndex)
        {
            var headerRow = sheetData.RawData[sheetData.HeaderRowIndex];
            sheetData.Headers = headerRow
                .Select(cell => NormalizeHeaderName(cell.StringValue))
                .ToList();
        }

        // Read data rows starting after header
        sheetData.Rows = ReadDataRows(sheetData, sheetData.HeaderRowIndex + 1);

        _logger.LogDebug(
            "Parsed sheet '{SheetName}' with {RowCount} data rows, {HeaderCount} headers",
            sheetData.Name,
            sheetData.Rows.Count,
            sheetData.Headers.Count);

        return Task.FromResult(sheetData);
    }

    private int CalculateHeaderScore(List<ExcelCellData> row)
    {
        var score = 0;
        var nonEmptyCells = row.Count(c => !c.IsEmpty);

        // Prefer rows with a reasonable number of non-empty cells
        if (nonEmptyCells >= 3)
        {
            score += nonEmptyCells * 2;
        }

        foreach (var cell in row)
        {
            if (cell.IsEmpty) continue;

            var cellText = cell.StringValue.ToLowerInvariant();

            // Check for common header keywords
            foreach (var keyword in CommonHeaderKeywords)
            {
                if (cellText.Contains(keyword))
                {
                    score += 10;
                    break;
                }
            }

            // Prefer text values over numbers for headers
            if (cell.Value is string)
            {
                score += 3;
            }

            // Check for typical header patterns
            if (Regex.IsMatch(cellText, @"^(item\s*)?no\.?$", RegexOptions.IgnoreCase))
            {
                score += 15;
            }

            if (Regex.IsMatch(cellText, @"^description$", RegexOptions.IgnoreCase))
            {
                score += 15;
            }

            if (Regex.IsMatch(cellText, @"^(qty|quantity)$", RegexOptions.IgnoreCase))
            {
                score += 15;
            }

            if (Regex.IsMatch(cellText, @"^(uom|unit)$", RegexOptions.IgnoreCase))
            {
                score += 15;
            }
        }

        return score;
    }

    private static string NormalizeHeaderName(string header)
    {
        if (string.IsNullOrWhiteSpace(header))
        {
            return string.Empty;
        }

        // Remove extra whitespace and normalize
        header = Regex.Replace(header.Trim(), @"\s+", " ");

        return header;
    }
}
