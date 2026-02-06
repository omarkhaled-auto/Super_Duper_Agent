using FluentValidation;

namespace Bayan.Application.Features.Documents.Commands.CreateFolder;

/// <summary>
/// Validator for CreateFolderCommand.
/// </summary>
public class CreateFolderCommandValidator : AbstractValidator<CreateFolderCommand>
{
    public CreateFolderCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.FolderName)
            .NotEmpty()
            .WithMessage("Folder name is required.")
            .MaximumLength(100)
            .WithMessage("Folder name must not exceed 100 characters.")
            .Must(BeValidFolderName)
            .WithMessage("Folder name contains invalid characters.");

        RuleFor(x => x.ParentPath)
            .MaximumLength(255)
            .WithMessage("Parent path must not exceed 255 characters.")
            .Must(BeValidPath!)
            .When(x => !string.IsNullOrEmpty(x.ParentPath))
            .WithMessage("Parent path contains invalid characters.");
    }

    /// <summary>
    /// Validates that the folder name doesn't contain invalid characters.
    /// </summary>
    private static bool BeValidFolderName(string folderName)
    {
        if (string.IsNullOrWhiteSpace(folderName))
            return false;

        // Check for path separator characters
        if (folderName.Contains('/') || folderName.Contains('\\'))
            return false;

        // Check for path traversal attempts
        if (folderName == "." || folderName == "..")
            return false;

        // Check for invalid characters
        var invalidChars = Path.GetInvalidFileNameChars();
        return !folderName.Any(c => invalidChars.Contains(c));
    }

    /// <summary>
    /// Validates that the parent path doesn't contain invalid characters.
    /// </summary>
    private static bool BeValidPath(string path)
    {
        if (string.IsNullOrWhiteSpace(path))
            return true; // Empty parent path is valid (root level)

        // Check for path traversal attempts
        if (path.Contains("..") || path.Contains("//"))
            return false;

        // Check for invalid characters
        var invalidChars = Path.GetInvalidPathChars();
        return !path.Any(c => invalidChars.Contains(c));
    }
}
