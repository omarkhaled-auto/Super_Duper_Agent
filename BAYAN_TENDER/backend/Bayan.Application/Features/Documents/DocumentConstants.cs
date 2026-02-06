namespace Bayan.Application.Features.Documents;

/// <summary>
/// Constants for document management.
/// </summary>
public static class DocumentConstants
{
    /// <summary>
    /// Default folders for tender document organization.
    /// These folders are automatically available for every tender.
    /// </summary>
    public static readonly IReadOnlyList<string> DefaultFolders = new[]
    {
        "RFP Package",
        "Drawings",
        "Specifications",
        "BOQ",
        "Contract Forms",
        "Addenda",
        "Clarifications"
    };

    /// <summary>
    /// Default URL expiry time for presigned download URLs.
    /// </summary>
    public static readonly TimeSpan DefaultPresignedUrlExpiry = TimeSpan.FromMinutes(15);

    /// <summary>
    /// Maximum file size allowed for upload (100 MB).
    /// </summary>
    public const long MaxFileSizeBytes = 100 * 1024 * 1024;

    /// <summary>
    /// Allowed file extensions for document uploads.
    /// </summary>
    public static readonly IReadOnlySet<string> AllowedExtensions = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
    {
        // Documents
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".csv", ".rtf", ".odt", ".ods", ".odp",
        // Images
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg",
        // Archives
        ".zip", ".rar", ".7z", ".tar", ".gz",
        // CAD/Engineering
        ".dwg", ".dxf", ".step", ".stp", ".iges", ".igs",
        // Data
        ".xml", ".json"
    };

    /// <summary>
    /// Storage path template for tender documents.
    /// {0} = tender ID, {1} = folder path
    /// </summary>
    public const string StoragePathTemplate = "{0}/{1}";
}
