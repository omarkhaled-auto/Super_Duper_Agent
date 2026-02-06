namespace Bayan.Application.Common.Services;

/// <summary>
/// Service for validating file uploads for security.
/// </summary>
public static class FileValidationService
{
    /// <summary>
    /// Allowed file extensions for document uploads.
    /// </summary>
    public static readonly HashSet<string> AllowedDocumentExtensions = new(StringComparer.OrdinalIgnoreCase)
    {
        // Documents
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
        ".txt",
        ".rtf",
        ".csv",

        // Images
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".webp",

        // Archives (for tender packages)
        ".zip",
        ".rar",
        ".7z"
    };

    /// <summary>
    /// Blocked file extensions that should never be allowed.
    /// </summary>
    public static readonly HashSet<string> BlockedExtensions = new(StringComparer.OrdinalIgnoreCase)
    {
        // Executables
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bat",
        ".cmd",
        ".sh",
        ".ps1",
        ".psm1",
        ".psd1",
        ".vbs",
        ".vbe",
        ".js",
        ".jse",
        ".ws",
        ".wsf",
        ".wsh",
        ".msi",
        ".msp",
        ".mst",
        ".com",
        ".scr",
        ".pif",
        ".cpl",
        ".hta",
        ".jar",

        // Web/Script files
        ".php",
        ".asp",
        ".aspx",
        ".jsp",
        ".py",
        ".rb",
        ".pl",
        ".cgi",

        // Configuration files that could be dangerous
        ".htaccess",
        ".htpasswd",
        ".config",
        ".ini",
        ".reg",

        // Shortcut/Link files
        ".lnk",
        ".scf",
        ".url",
        ".inf"
    };

    /// <summary>
    /// Content type mapping for allowed extensions.
    /// </summary>
    public static readonly Dictionary<string, string[]> AllowedContentTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        { ".pdf", new[] { "application/pdf" } },
        { ".doc", new[] { "application/msword" } },
        { ".docx", new[] { "application/vnd.openxmlformats-officedocument.wordprocessingml.document" } },
        { ".xls", new[] { "application/vnd.ms-excel" } },
        { ".xlsx", new[] { "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" } },
        { ".ppt", new[] { "application/vnd.ms-powerpoint" } },
        { ".pptx", new[] { "application/vnd.openxmlformats-officedocument.presentationml.presentation" } },
        { ".txt", new[] { "text/plain" } },
        { ".rtf", new[] { "application/rtf", "text/rtf" } },
        { ".csv", new[] { "text/csv", "application/csv" } },
        { ".jpg", new[] { "image/jpeg" } },
        { ".jpeg", new[] { "image/jpeg" } },
        { ".png", new[] { "image/png" } },
        { ".gif", new[] { "image/gif" } },
        { ".bmp", new[] { "image/bmp" } },
        { ".tiff", new[] { "image/tiff" } },
        { ".webp", new[] { "image/webp" } },
        { ".zip", new[] { "application/zip", "application/x-zip-compressed" } },
        { ".rar", new[] { "application/x-rar-compressed", "application/vnd.rar" } },
        { ".7z", new[] { "application/x-7z-compressed" } }
    };

    /// <summary>
    /// Maximum file size in bytes (50 MB default).
    /// </summary>
    public const long MaxFileSizeBytes = 50 * 1024 * 1024;

    /// <summary>
    /// Validates a file for upload.
    /// </summary>
    /// <param name="fileName">The original file name.</param>
    /// <param name="contentType">The content type of the file.</param>
    /// <param name="fileSize">The size of the file in bytes.</param>
    /// <param name="maxSizeBytes">Optional maximum file size override.</param>
    /// <returns>Validation result with success status and error message if any.</returns>
    public static FileValidationResult ValidateFile(
        string fileName,
        string contentType,
        long fileSize,
        long? maxSizeBytes = null)
    {
        var maxSize = maxSizeBytes ?? MaxFileSizeBytes;

        // Check file size
        if (fileSize <= 0)
        {
            return FileValidationResult.Failure("File is empty.");
        }

        if (fileSize > maxSize)
        {
            return FileValidationResult.Failure(
                $"File size ({fileSize / (1024 * 1024):F2} MB) exceeds the maximum allowed size ({maxSize / (1024 * 1024)} MB).");
        }

        // Get and validate extension
        var extension = Path.GetExtension(fileName)?.ToLowerInvariant();

        if (string.IsNullOrEmpty(extension))
        {
            return FileValidationResult.Failure("File must have an extension.");
        }

        // Check if extension is explicitly blocked
        if (BlockedExtensions.Contains(extension))
        {
            return FileValidationResult.Failure($"File type '{extension}' is not allowed for security reasons.");
        }

        // Check if extension is allowed
        if (!AllowedDocumentExtensions.Contains(extension))
        {
            return FileValidationResult.Failure(
                $"File type '{extension}' is not allowed. Allowed types: {string.Join(", ", AllowedDocumentExtensions)}");
        }

        // Validate content type matches extension (if we have mapping)
        if (AllowedContentTypes.TryGetValue(extension, out var allowedTypes))
        {
            if (!allowedTypes.Contains(contentType, StringComparer.OrdinalIgnoreCase))
            {
                return FileValidationResult.Failure(
                    $"Content type '{contentType}' does not match the expected type for '{extension}' files.");
            }
        }

        // Sanitize file name (remove path traversal attempts)
        var sanitizedName = SanitizeFileName(fileName);
        if (string.IsNullOrEmpty(sanitizedName))
        {
            return FileValidationResult.Failure("Invalid file name.");
        }

        return FileValidationResult.Success(sanitizedName);
    }

    /// <summary>
    /// Sanitizes a file name by removing path traversal characters and invalid characters.
    /// </summary>
    /// <param name="fileName">The original file name.</param>
    /// <returns>The sanitized file name.</returns>
    public static string SanitizeFileName(string fileName)
    {
        if (string.IsNullOrWhiteSpace(fileName))
        {
            return string.Empty;
        }

        // Get just the file name (remove any path components)
        fileName = Path.GetFileName(fileName);

        // Remove any path traversal sequences
        fileName = fileName.Replace("..", string.Empty);
        fileName = fileName.Replace("/", string.Empty);
        fileName = fileName.Replace("\\", string.Empty);

        // Remove invalid characters
        var invalidChars = Path.GetInvalidFileNameChars();
        foreach (var c in invalidChars)
        {
            fileName = fileName.Replace(c.ToString(), string.Empty);
        }

        // Ensure the file name is not too long
        if (fileName.Length > 255)
        {
            var ext = Path.GetExtension(fileName);
            var name = Path.GetFileNameWithoutExtension(fileName);
            var maxNameLength = 255 - ext.Length;
            fileName = name.Substring(0, maxNameLength) + ext;
        }

        return fileName.Trim();
    }

    /// <summary>
    /// Generates a safe storage path for a file.
    /// </summary>
    /// <param name="basePath">The base storage path.</param>
    /// <param name="fileName">The file name.</param>
    /// <returns>A safe storage path with a unique identifier.</returns>
    public static string GenerateSafeStoragePath(string basePath, string fileName)
    {
        var sanitizedName = SanitizeFileName(fileName);
        var uniqueId = Guid.NewGuid().ToString("N")[..8];
        var extension = Path.GetExtension(sanitizedName);
        var nameWithoutExt = Path.GetFileNameWithoutExtension(sanitizedName);

        return Path.Combine(basePath, $"{nameWithoutExt}_{uniqueId}{extension}").Replace("\\", "/");
    }
}

/// <summary>
/// Result of file validation.
/// </summary>
public class FileValidationResult
{
    public bool IsValid { get; private init; }
    public string? ErrorMessage { get; private init; }
    public string? SanitizedFileName { get; private init; }

    private FileValidationResult() { }

    public static FileValidationResult Success(string sanitizedFileName) =>
        new() { IsValid = true, SanitizedFileName = sanitizedFileName };

    public static FileValidationResult Failure(string errorMessage) =>
        new() { IsValid = false, ErrorMessage = errorMessage };
}
