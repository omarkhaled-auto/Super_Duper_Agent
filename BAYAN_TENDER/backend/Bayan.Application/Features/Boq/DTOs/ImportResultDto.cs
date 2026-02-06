namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// DTO for the final import execution result.
/// </summary>
public record ImportResultDto
{
    /// <summary>
    /// Whether the import was successful.
    /// </summary>
    public bool Success { get; init; }

    /// <summary>
    /// Number of sections created.
    /// </summary>
    public int ImportedSections { get; init; }

    /// <summary>
    /// Number of items created.
    /// </summary>
    public int ImportedItems { get; init; }

    /// <summary>
    /// Number of rows skipped.
    /// </summary>
    public int SkippedRows { get; init; }

    /// <summary>
    /// The tender ID the BOQ was imported into.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// Path to the stored original file in MinIO.
    /// </summary>
    public string? OriginalFilePath { get; init; }

    /// <summary>
    /// Detailed results for each created section.
    /// </summary>
    public List<ImportedSectionResult> Sections { get; init; } = new();

    /// <summary>
    /// Import timestamp.
    /// </summary>
    public DateTime ImportedAt { get; init; }

    /// <summary>
    /// User who performed the import.
    /// </summary>
    public Guid? ImportedBy { get; init; }

    /// <summary>
    /// Error message if import failed.
    /// </summary>
    public string? ErrorMessage { get; init; }

    /// <summary>
    /// Warnings that occurred during import.
    /// </summary>
    public List<string> Warnings { get; init; } = new();
}

/// <summary>
/// Result details for an imported section.
/// </summary>
public record ImportedSectionResult
{
    /// <summary>
    /// The created section ID.
    /// </summary>
    public Guid SectionId { get; init; }

    /// <summary>
    /// Section number.
    /// </summary>
    public string SectionNumber { get; init; } = string.Empty;

    /// <summary>
    /// Section title.
    /// </summary>
    public string Title { get; init; } = string.Empty;

    /// <summary>
    /// Number of items in this section.
    /// </summary>
    public int ItemCount { get; init; }

    /// <summary>
    /// Child sections under this section.
    /// </summary>
    public List<ImportedSectionResult> ChildSections { get; init; } = new();
}

/// <summary>
/// Request DTO for executing the import.
/// </summary>
public record ExecuteBoqImportRequest
{
    /// <summary>
    /// The import session ID from the upload step.
    /// </summary>
    public Guid ImportSessionId { get; init; }

    /// <summary>
    /// Whether to clear existing BOQ data before import.
    /// </summary>
    public bool ClearExisting { get; init; }

    /// <summary>
    /// Optional default section title for items without detected sections.
    /// </summary>
    public string? DefaultSectionTitle { get; init; }

    /// <summary>
    /// Whether to skip rows with validation warnings.
    /// </summary>
    public bool SkipWarnings { get; init; }
}
