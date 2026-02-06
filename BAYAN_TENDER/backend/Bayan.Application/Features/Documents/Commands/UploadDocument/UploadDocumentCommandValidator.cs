using FluentValidation;

namespace Bayan.Application.Features.Documents.Commands.UploadDocument;

/// <summary>
/// Validator for UploadDocumentCommand.
/// </summary>
public class UploadDocumentCommandValidator : AbstractValidator<UploadDocumentCommand>
{
    /// <summary>
    /// Maximum allowed file size (100 MB).
    /// </summary>
    private const long MaxFileSizeBytes = 100 * 1024 * 1024;

    /// <summary>
    /// Allowed file extensions.
    /// </summary>
    private static readonly HashSet<string> AllowedExtensions = new(StringComparer.OrdinalIgnoreCase)
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

    public UploadDocumentCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.FileName)
            .NotEmpty()
            .WithMessage("File name is required.")
            .MaximumLength(255)
            .WithMessage("File name must not exceed 255 characters.")
            .Must(HaveValidExtension)
            .WithMessage($"File type is not allowed. Allowed types: {string.Join(", ", AllowedExtensions)}");

        RuleFor(x => x.FileStream)
            .NotNull()
            .WithMessage("File content is required.");

        RuleFor(x => x.FileSize)
            .GreaterThan(0)
            .WithMessage("File cannot be empty.")
            .LessThanOrEqualTo(MaxFileSizeBytes)
            .WithMessage($"File size must not exceed {MaxFileSizeBytes / (1024 * 1024)} MB.");

        RuleFor(x => x.FolderPath)
            .NotEmpty()
            .WithMessage("Folder path is required.")
            .MaximumLength(255)
            .WithMessage("Folder path must not exceed 255 characters.")
            .Must(BeValidFolderPath)
            .WithMessage("Folder path contains invalid characters.");

        RuleFor(x => x.ContentType)
            .NotEmpty()
            .WithMessage("Content type is required.");
    }

    /// <summary>
    /// Validates that the file has an allowed extension.
    /// </summary>
    private static bool HaveValidExtension(string fileName)
    {
        if (string.IsNullOrWhiteSpace(fileName))
            return false;

        var extension = Path.GetExtension(fileName);
        return AllowedExtensions.Contains(extension);
    }

    /// <summary>
    /// Validates that the folder path doesn't contain invalid characters.
    /// </summary>
    private static bool BeValidFolderPath(string folderPath)
    {
        if (string.IsNullOrWhiteSpace(folderPath))
            return false;

        // Check for path traversal attempts
        if (folderPath.Contains("..") || folderPath.Contains("//"))
            return false;

        // Check for invalid characters
        var invalidChars = Path.GetInvalidPathChars();
        return !folderPath.Any(c => invalidChars.Contains(c));
    }
}
