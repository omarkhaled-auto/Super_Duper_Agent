namespace Bayan.Application.Features.Evaluation.DTOs;

/// <summary>
/// DTO for award pack generation result.
/// </summary>
public class AwardPackDto
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Tender reference.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Tender title.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// File path in MinIO storage.
    /// </summary>
    public string FilePath { get; set; } = string.Empty;

    /// <summary>
    /// File name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Download URL (presigned).
    /// </summary>
    public string DownloadUrl { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSizeBytes { get; set; }

    /// <summary>
    /// When the award pack was generated.
    /// </summary>
    public DateTime GeneratedAt { get; set; }

    /// <summary>
    /// User who generated the award pack.
    /// </summary>
    public Guid GeneratedBy { get; set; }

    /// <summary>
    /// Name of user who generated the award pack.
    /// </summary>
    public string GeneratedByName { get; set; } = string.Empty;
}

/// <summary>
/// DTO for award pack generation request.
/// </summary>
public class GenerateAwardPackRequestDto
{
    /// <summary>
    /// Whether to include technical evaluation details.
    /// </summary>
    public bool IncludeTechnicalDetails { get; set; } = true;

    /// <summary>
    /// Whether to include commercial evaluation details.
    /// </summary>
    public bool IncludeCommercialDetails { get; set; } = true;

    /// <summary>
    /// Whether to include sensitivity analysis.
    /// </summary>
    public bool IncludeSensitivityAnalysis { get; set; } = true;

    /// <summary>
    /// Whether to include bid exceptions.
    /// </summary>
    public bool IncludeExceptions { get; set; } = true;

    /// <summary>
    /// Custom executive summary (optional).
    /// </summary>
    public string? ExecutiveSummary { get; set; }

    /// <summary>
    /// Custom recommendation notes (optional).
    /// </summary>
    public string? RecommendationNotes { get; set; }
}

/// <summary>
/// DTO for downloading the award pack.
/// </summary>
public class AwardPackDownloadDto
{
    /// <summary>
    /// File content as byte array.
    /// </summary>
    public byte[] FileContent { get; set; } = Array.Empty<byte>();

    /// <summary>
    /// File name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Content type.
    /// </summary>
    public string ContentType { get; set; } = "application/pdf";
}
