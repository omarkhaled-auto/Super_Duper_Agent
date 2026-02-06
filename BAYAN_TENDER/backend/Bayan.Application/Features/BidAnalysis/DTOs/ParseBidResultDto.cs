namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Result of parsing a bid file.
/// </summary>
public class ParseBidResultDto
{
    /// <summary>
    /// Whether parsing was successful.
    /// </summary>
    public bool Success { get; set; }

    /// <summary>
    /// Error message if parsing failed.
    /// </summary>
    public string? ErrorMessage { get; set; }

    /// <summary>
    /// List of sheets found in the file.
    /// </summary>
    public List<SheetInfoDto> Sheets { get; set; } = new();

    /// <summary>
    /// Detected columns in the primary sheet.
    /// </summary>
    public List<ColumnInfoDto> Columns { get; set; } = new();

    /// <summary>
    /// Preview of the first few rows.
    /// </summary>
    public List<Dictionary<string, object?>> PreviewRows { get; set; } = new();

    /// <summary>
    /// Total count of items (rows) detected.
    /// </summary>
    public int ItemCount { get; set; }

    /// <summary>
    /// Suggested column mappings based on header detection.
    /// </summary>
    public ColumnMappingsDto SuggestedMappings { get; set; } = new();

    /// <summary>
    /// Detected header row index.
    /// </summary>
    public int HeaderRowIndex { get; set; }
}

/// <summary>
/// Information about an Excel sheet.
/// </summary>
public class SheetInfoDto
{
    /// <summary>
    /// Sheet name.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Sheet index (0-based).
    /// </summary>
    public int Index { get; set; }

    /// <summary>
    /// Number of rows in the sheet.
    /// </summary>
    public int RowCount { get; set; }

    /// <summary>
    /// Number of columns in the sheet.
    /// </summary>
    public int ColumnCount { get; set; }
}

/// <summary>
/// Information about a detected column.
/// </summary>
public class ColumnInfoDto
{
    /// <summary>
    /// Column index (0-based).
    /// </summary>
    public int Index { get; set; }

    /// <summary>
    /// Column letter (A, B, C, etc.).
    /// </summary>
    public string Letter { get; set; } = string.Empty;

    /// <summary>
    /// Column header text.
    /// </summary>
    public string Header { get; set; } = string.Empty;

    /// <summary>
    /// Detected data type of the column.
    /// </summary>
    public string DataType { get; set; } = "string";

    /// <summary>
    /// Sample values from the column.
    /// </summary>
    public List<string> SampleValues { get; set; } = new();

    /// <summary>
    /// Suggested field mapping.
    /// </summary>
    public string? SuggestedMapping { get; set; }
}
