using Bayan.Application.Common.Interfaces;

namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// DTO for BOQ template export request.
/// </summary>
public class ExportBoqTemplateDto
{
    /// <summary>
    /// Tender ID for which to export the BOQ template.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Columns to include in the export.
    /// Default: ItemNumber, Description, Quantity, Uom, UnitRate, Amount
    /// </summary>
    public List<string> IncludeColumns { get; set; } = new()
    {
        "Section", "ItemNumber", "Description", "Quantity", "Uom", "UnitRate", "Amount"
    };

    /// <summary>
    /// Columns to lock (read-only) in the exported template.
    /// Default: ItemNumber, Description, Quantity, Uom
    /// </summary>
    public List<string> LockColumns { get; set; } = new()
    {
        "ItemNumber", "Description", "Quantity", "Uom"
    };

    /// <summary>
    /// Whether to include an instructions sheet with guidance.
    /// </summary>
    public bool IncludeInstructions { get; set; } = true;

    /// <summary>
    /// Language for the template.
    /// </summary>
    public TemplateLanguage Language { get; set; } = TemplateLanguage.English;
}
