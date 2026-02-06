namespace Bayan.Application.Features.BidAnalysis.DTOs;

/// <summary>
/// Data transfer object for importing bid data with column mappings.
/// </summary>
public class ImportBidDto
{
    /// <summary>
    /// Column mappings from Excel columns to bid fields.
    /// </summary>
    public ColumnMappingsDto ColumnMappings { get; set; } = new();

    /// <summary>
    /// Bid items extracted from the file.
    /// </summary>
    public List<ImportBidItemDto> Items { get; set; } = new();
}

/// <summary>
/// Column mappings configuration for bid import.
/// </summary>
public class ColumnMappingsDto
{
    /// <summary>
    /// Excel column name/index for item number.
    /// </summary>
    public string? ItemNumberColumn { get; set; }

    /// <summary>
    /// Excel column name/index for description.
    /// </summary>
    public string? DescriptionColumn { get; set; }

    /// <summary>
    /// Excel column name/index for quantity.
    /// </summary>
    public string? QuantityColumn { get; set; }

    /// <summary>
    /// Excel column name/index for unit of measurement.
    /// </summary>
    public string? UomColumn { get; set; }

    /// <summary>
    /// Excel column name/index for unit rate.
    /// </summary>
    public string? UnitRateColumn { get; set; }

    /// <summary>
    /// Excel column name/index for total amount.
    /// </summary>
    public string? AmountColumn { get; set; }

    /// <summary>
    /// Excel column name/index for currency.
    /// </summary>
    public string? CurrencyColumn { get; set; }

    /// <summary>
    /// Default currency if not specified per row.
    /// </summary>
    public string DefaultCurrency { get; set; } = "AED";

    /// <summary>
    /// Row index to start reading data from (0-based, after header).
    /// </summary>
    public int StartRowIndex { get; set; }

    /// <summary>
    /// Sheet name or index to read from.
    /// </summary>
    public string? SheetName { get; set; }

    /// <summary>
    /// Sheet index to read from (0-based).
    /// </summary>
    public int SheetIndex { get; set; }
}

/// <summary>
/// Represents a single bid item during import.
/// </summary>
public class ImportBidItemDto
{
    /// <summary>
    /// Row index in the source file.
    /// </summary>
    public int RowIndex { get; set; }

    /// <summary>
    /// Item number from the bid.
    /// </summary>
    public string? ItemNumber { get; set; }

    /// <summary>
    /// Item description.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Quantity.
    /// </summary>
    public decimal? Quantity { get; set; }

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    public string? Uom { get; set; }

    /// <summary>
    /// Unit rate.
    /// </summary>
    public decimal? UnitRate { get; set; }

    /// <summary>
    /// Total amount.
    /// </summary>
    public decimal? Amount { get; set; }

    /// <summary>
    /// Currency code.
    /// </summary>
    public string? Currency { get; set; }

    /// <summary>
    /// Raw cell values for reference.
    /// </summary>
    public Dictionary<string, object?> RawValues { get; set; } = new();
}
