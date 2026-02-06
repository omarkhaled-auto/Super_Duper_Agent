using FluentValidation;

namespace Bayan.Application.Features.Boq.Commands.UploadBoqImportFile;

/// <summary>
/// Validator for UploadBoqImportFileCommand.
/// </summary>
public class UploadBoqImportFileCommandValidator : AbstractValidator<UploadBoqImportFileCommand>
{
    private static readonly string[] AllowedContentTypes = new[]
    {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
        "application/vnd.ms-excel", // .xls
        "application/octet-stream" // fallback
    };

    private static readonly string[] AllowedExtensions = new[] { ".xlsx", ".xls" };

    public UploadBoqImportFileCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.FileStream)
            .NotNull()
            .WithMessage("File stream is required.");

        RuleFor(x => x.FileName)
            .NotEmpty()
            .WithMessage("File name is required.")
            .Must(HaveValidExtension)
            .WithMessage("File must be an Excel file (.xlsx or .xls).");

        RuleFor(x => x.FileSize)
            .GreaterThan(0)
            .WithMessage("File cannot be empty.")
            .LessThanOrEqualTo(50 * 1024 * 1024) // 50MB max
            .WithMessage("File size cannot exceed 50MB.");

        RuleFor(x => x.ContentType)
            .Must(BeValidContentType)
            .When(x => !string.IsNullOrEmpty(x.ContentType))
            .WithMessage("Invalid file type. Only Excel files are allowed.");
    }

    private bool HaveValidExtension(string fileName)
    {
        if (string.IsNullOrEmpty(fileName))
            return false;

        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        return AllowedExtensions.Contains(extension);
    }

    private bool BeValidContentType(string contentType)
    {
        return AllowedContentTypes.Contains(contentType.ToLowerInvariant());
    }
}
