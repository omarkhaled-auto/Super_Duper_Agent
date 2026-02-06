using Bayan.Application.Features.Boq.DTOs;

namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Service interface for exporting BOQ templates to Excel.
/// </summary>
public interface ITemplateExportService
{
    /// <summary>
    /// Generates an Excel BOQ template for a tender.
    /// </summary>
    /// <param name="request">Export request parameters.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Export result containing the Excel file content.</returns>
    Task<ExportResultDto> GenerateBoqTemplateAsync(
        BoqTemplateGenerationRequest request,
        CancellationToken cancellationToken = default);
}

/// <summary>
/// Request parameters for BOQ template generation.
/// </summary>
public class BoqTemplateGenerationRequest
{
    /// <summary>
    /// Tender ID for the BOQ template.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender title for the header.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Tender reference number for the header.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Submission deadline for the header.
    /// </summary>
    public DateTime SubmissionDeadline { get; set; }

    /// <summary>
    /// Currency code for the tender.
    /// </summary>
    public string Currency { get; set; } = "AED";

    /// <summary>
    /// BOQ sections with items.
    /// </summary>
    public List<BoqSectionExportDto> Sections { get; set; } = new();

    /// <summary>
    /// Available UOM values for the dropdown.
    /// </summary>
    public List<string> AvailableUoms { get; set; } = new();

    /// <summary>
    /// Columns to include in the export.
    /// </summary>
    public List<string> IncludeColumns { get; set; } = new()
    {
        "ItemNumber", "Description", "Quantity", "Uom", "UnitRate", "Amount"
    };

    /// <summary>
    /// Columns to lock (read-only).
    /// </summary>
    public List<string> LockColumns { get; set; } = new()
    {
        "ItemNumber", "Description", "Quantity", "Uom"
    };

    /// <summary>
    /// Whether to include an instructions sheet.
    /// </summary>
    public bool IncludeInstructions { get; set; } = true;

    /// <summary>
    /// Language for the template (English, Arabic, or Both).
    /// </summary>
    public TemplateLanguage Language { get; set; } = TemplateLanguage.English;
}

/// <summary>
/// BOQ section data for export.
/// </summary>
public class BoqSectionExportDto
{
    /// <summary>
    /// Section number (e.g., "1", "1.1").
    /// </summary>
    public string SectionNumber { get; set; } = string.Empty;

    /// <summary>
    /// Section title.
    /// </summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Items in this section.
    /// </summary>
    public List<BoqItemExportDto> Items { get; set; } = new();
}

/// <summary>
/// BOQ item data for export.
/// </summary>
public class BoqItemExportDto
{
    /// <summary>
    /// Item number (e.g., "1.1.1").
    /// </summary>
    public string ItemNumber { get; set; } = string.Empty;

    /// <summary>
    /// Item description.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Quantity.
    /// </summary>
    public decimal Quantity { get; set; }

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Optional notes.
    /// </summary>
    public string? Notes { get; set; }
}

/// <summary>
/// Template language options.
/// </summary>
public enum TemplateLanguage
{
    /// <summary>
    /// English only.
    /// </summary>
    English = 0,

    /// <summary>
    /// Arabic only.
    /// </summary>
    Arabic = 1,

    /// <summary>
    /// Both English and Arabic (bilingual).
    /// </summary>
    Both = 2
}
