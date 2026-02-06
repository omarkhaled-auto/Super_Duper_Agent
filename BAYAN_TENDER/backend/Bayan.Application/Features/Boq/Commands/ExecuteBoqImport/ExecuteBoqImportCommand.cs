using Bayan.Application.Features.Boq.DTOs;
using MediatR;

namespace Bayan.Application.Features.Boq.Commands.ExecuteBoqImport;

/// <summary>
/// Command to execute the BOQ import after validation.
/// </summary>
public class ExecuteBoqImportCommand : IRequest<ImportResultDto>
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
    /// Whether to clear existing BOQ data before import.
    /// </summary>
    public bool ClearExisting { get; set; }

    /// <summary>
    /// Optional default section title for items without detected sections.
    /// </summary>
    public string? DefaultSectionTitle { get; set; }

    /// <summary>
    /// Whether to skip rows with validation warnings.
    /// </summary>
    public bool SkipWarnings { get; set; }

    /// <summary>
    /// Original file stream for storage (optional - if not provided, file won't be stored).
    /// </summary>
    public Stream? OriginalFileStream { get; set; }

    /// <summary>
    /// Original file name (for storage).
    /// </summary>
    public string? OriginalFileName { get; set; }

    /// <summary>
    /// Content type (for storage).
    /// </summary>
    public string? ContentType { get; set; }
}
