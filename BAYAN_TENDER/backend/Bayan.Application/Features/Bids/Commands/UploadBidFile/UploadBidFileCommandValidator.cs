using FluentValidation;

namespace Bayan.Application.Features.Bids.Commands.UploadBidFile;

/// <summary>
/// Validator for UploadBidFileCommand.
/// </summary>
public class UploadBidFileCommandValidator : AbstractValidator<UploadBidFileCommand>
{
    /// <summary>
    /// Maximum allowed file size (100 MB).
    /// </summary>
    private const long MaxFileSizeBytes = 100 * 1024 * 1024;

    /// <summary>
    /// Allowed file extensions for bid documents.
    /// </summary>
    private static readonly HashSet<string> AllowedExtensions = new(StringComparer.OrdinalIgnoreCase)
    {
        // Documents
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".csv", ".rtf", ".odt", ".ods", ".odp",
        // Images
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff",
        // Archives
        ".zip", ".rar", ".7z",
        // Data
        ".xml", ".json"
    };

    public UploadBidFileCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidderId)
            .NotEmpty()
            .WithMessage("Bidder ID is required.");

        RuleFor(x => x.DocumentType)
            .IsInEnum()
            .WithMessage("Invalid document type.");

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
}
