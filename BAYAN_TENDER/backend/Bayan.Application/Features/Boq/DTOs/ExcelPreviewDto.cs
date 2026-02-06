namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// DTO for Excel file preview data returned after upload.
/// </summary>
public record ExcelPreviewDto
{
    /// <summary>
    /// Unique identifier for this import session.
    /// </summary>
    public Guid ImportSessionId { get; init; }

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; init; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSizeBytes { get; init; }

    /// <summary>
    /// Detected column headers from the Excel file.
    /// </summary>
    public List<ExcelColumnDto> Columns { get; init; } = new();

    /// <summary>
    /// Preview rows (first 10 rows of data).
    /// </summary>
    public List<Dictionary<string, object?>> PreviewRows { get; init; } = new();

    /// <summary>
    /// Total number of data rows in the file.
    /// </summary>
    public int TotalRowCount { get; init; }

    /// <summary>
    /// Row index where the header was detected (zero-based).
    /// </summary>
    public int HeaderRowIndex { get; init; }

    /// <summary>
    /// Name of the sheet being used.
    /// </summary>
    public string SheetName { get; init; } = string.Empty;

    /// <summary>
    /// List of all sheet names in the file.
    /// </summary>
    public List<string> AvailableSheets { get; init; } = new();

    /// <summary>
    /// Suggested column mappings based on header analysis.
    /// </summary>
    public List<ColumnMappingDto> SuggestedMappings { get; init; } = new();
}

/// <summary>
/// DTO representing a column in the Excel file.
/// </summary>
public record ExcelColumnDto
{
    /// <summary>
    /// Column index (zero-based).
    /// </summary>
    public int Index { get; init; }

    /// <summary>
    /// Column header text.
    /// </summary>
    public string Header { get; init; } = string.Empty;

    /// <summary>
    /// Sample values from the column (up to 5).
    /// </summary>
    public List<string> SampleValues { get; init; } = new();

    /// <summary>
    /// Detected data type of the column.
    /// </summary>
    public string DataType { get; init; } = "string";

    /// <summary>
    /// Percentage of non-empty values in the column.
    /// </summary>
    public double FillRate { get; init; }
}
