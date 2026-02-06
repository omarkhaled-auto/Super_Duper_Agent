namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for Excel file parsing operations.
/// </summary>
public interface IExcelService
{
    /// <summary>
    /// Parses an Excel file and returns the result.
    /// </summary>
    /// <param name="stream">The Excel file stream.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The parsed Excel result containing headers and rows.</returns>
    Task<ExcelParseResult> ParseExcelFileAsync(
        Stream stream,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Detects the header row in a worksheet.
    /// </summary>
    /// <param name="sheet">The Excel sheet data.</param>
    /// <returns>The zero-based row index of the header row.</returns>
    int DetectHeaderRow(ExcelSheetData sheet);

    /// <summary>
    /// Reads data rows from a worksheet starting from a specific row.
    /// </summary>
    /// <param name="sheet">The Excel sheet data.</param>
    /// <param name="startRow">The starting row index (zero-based).</param>
    /// <returns>List of dictionaries representing each row with column headers as keys.</returns>
    List<Dictionary<string, object?>> ReadDataRows(ExcelSheetData sheet, int startRow);
}

/// <summary>
/// Represents the result of parsing an Excel file.
/// </summary>
public class ExcelParseResult
{
    /// <summary>
    /// List of sheets in the Excel file.
    /// </summary>
    public List<ExcelSheetData> Sheets { get; set; } = new();

    /// <summary>
    /// The first sheet's headers (convenience property).
    /// </summary>
    public List<string> Headers => Sheets.FirstOrDefault()?.Headers ?? new List<string>();

    /// <summary>
    /// The first sheet's data rows (convenience property).
    /// </summary>
    public List<Dictionary<string, object?>> Rows => Sheets.FirstOrDefault()?.Rows ?? new List<Dictionary<string, object?>>();

    /// <summary>
    /// Whether the parsing was successful.
    /// </summary>
    public bool Success { get; set; }

    /// <summary>
    /// Error message if parsing failed.
    /// </summary>
    public string? ErrorMessage { get; set; }
}

/// <summary>
/// Represents data from a single Excel sheet.
/// </summary>
public class ExcelSheetData
{
    /// <summary>
    /// Name of the sheet.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Index of the sheet (zero-based).
    /// </summary>
    public int Index { get; set; }

    /// <summary>
    /// Column headers from the header row.
    /// </summary>
    public List<string> Headers { get; set; } = new();

    /// <summary>
    /// Row index where the header was detected (zero-based).
    /// </summary>
    public int HeaderRowIndex { get; set; }

    /// <summary>
    /// Data rows as dictionaries with column headers as keys.
    /// </summary>
    public List<Dictionary<string, object?>> Rows { get; set; } = new();

    /// <summary>
    /// Raw cell data for advanced processing.
    /// </summary>
    public List<List<ExcelCellData>> RawData { get; set; } = new();

    /// <summary>
    /// Total number of rows (including empty rows).
    /// </summary>
    public int TotalRows { get; set; }

    /// <summary>
    /// Total number of columns.
    /// </summary>
    public int TotalColumns { get; set; }
}

/// <summary>
/// Represents data from a single Excel cell.
/// </summary>
public class ExcelCellData
{
    /// <summary>
    /// Row index (zero-based).
    /// </summary>
    public int Row { get; set; }

    /// <summary>
    /// Column index (zero-based).
    /// </summary>
    public int Column { get; set; }

    /// <summary>
    /// Cell value.
    /// </summary>
    public object? Value { get; set; }

    /// <summary>
    /// Cell value as string.
    /// </summary>
    public string StringValue => Value?.ToString()?.Trim() ?? string.Empty;

    /// <summary>
    /// Whether the cell is part of a merged range.
    /// </summary>
    public bool IsMerged { get; set; }

    /// <summary>
    /// Whether this cell is empty.
    /// </summary>
    public bool IsEmpty => Value == null || string.IsNullOrWhiteSpace(StringValue);
}
