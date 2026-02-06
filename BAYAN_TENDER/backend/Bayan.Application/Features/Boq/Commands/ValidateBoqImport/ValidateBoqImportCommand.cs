using Bayan.Application.Features.Boq.DTOs;
using MediatR;

namespace Bayan.Application.Features.Boq.Commands.ValidateBoqImport;

/// <summary>
/// Command to validate BOQ import data with column mappings.
/// </summary>
public class ValidateBoqImportCommand : IRequest<ImportValidationResultDto>
{
    /// <summary>
    /// ID of the tender to import BOQ data into.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The import session ID from the upload step.
    /// </summary>
    public Guid ImportSessionId { get; set; }

    /// <summary>
    /// The column mappings to use for import.
    /// </summary>
    public List<ColumnMappingDto> Mappings { get; set; } = new();

    /// <summary>
    /// Optional: Sheet index to import from (default: 0).
    /// </summary>
    public int SheetIndex { get; set; }

    /// <summary>
    /// Optional: Override the detected header row.
    /// </summary>
    public int? HeaderRowOverride { get; set; }
}
