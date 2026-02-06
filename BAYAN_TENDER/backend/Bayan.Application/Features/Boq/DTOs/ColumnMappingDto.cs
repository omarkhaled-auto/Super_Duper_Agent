namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// DTO for mapping an Excel column to a BOQ field.
/// </summary>
public record ColumnMappingDto
{
    /// <summary>
    /// The Excel column header or index.
    /// </summary>
    public string ExcelColumn { get; init; } = string.Empty;

    /// <summary>
    /// The target BOQ field to map to.
    /// </summary>
    public BoqField BoqField { get; init; }

    /// <summary>
    /// Confidence score of the suggested mapping (0-100).
    /// Only populated for suggested mappings.
    /// </summary>
    public int? Confidence { get; init; }

    /// <summary>
    /// Whether this mapping was auto-detected.
    /// </summary>
    public bool IsAutoDetected { get; init; }
}

/// <summary>
/// Available BOQ fields for column mapping.
/// </summary>
public enum BoqField
{
    /// <summary>
    /// Not mapped to any field.
    /// </summary>
    None = 0,

    /// <summary>
    /// Item number (e.g., "1.1", "1.2.1").
    /// </summary>
    ItemNumber = 1,

    /// <summary>
    /// Item description.
    /// </summary>
    Description = 2,

    /// <summary>
    /// Quantity.
    /// </summary>
    Quantity = 3,

    /// <summary>
    /// Unit of measurement code.
    /// </summary>
    Uom = 4,

    /// <summary>
    /// Section title/name.
    /// </summary>
    SectionTitle = 5,

    /// <summary>
    /// Additional notes.
    /// </summary>
    Notes = 6,

    /// <summary>
    /// Unit rate (for reference only).
    /// </summary>
    UnitRate = 7,

    /// <summary>
    /// Total amount (for reference only).
    /// </summary>
    Amount = 8,

    /// <summary>
    /// Specification reference.
    /// </summary>
    Specification = 9
}

/// <summary>
/// Request DTO for setting column mappings during import.
/// </summary>
public record SetColumnMappingsRequest
{
    /// <summary>
    /// The import session ID from the upload step.
    /// </summary>
    public Guid ImportSessionId { get; init; }

    /// <summary>
    /// The column mappings to use.
    /// </summary>
    public List<ColumnMappingDto> Mappings { get; init; } = new();

    /// <summary>
    /// Optional: Sheet index to import from (if multiple sheets).
    /// </summary>
    public int? SheetIndex { get; init; }

    /// <summary>
    /// Optional: Override the detected header row.
    /// </summary>
    public int? HeaderRowOverride { get; init; }
}
