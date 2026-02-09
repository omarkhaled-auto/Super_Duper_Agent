using FluentValidation;

namespace Bayan.Application.Features.Boq.Commands.ExportBoqTemplate;

/// <summary>
/// Validator for ExportBoqTemplateCommand.
/// </summary>
public class ExportBoqTemplateCommandValidator : AbstractValidator<ExportBoqTemplateCommand>
{
    /// <summary>
    /// Allowed column names for BOQ export.
    /// </summary>
    private static readonly HashSet<string> AllowedColumns = new(StringComparer.OrdinalIgnoreCase)
    {
        "Section", "ItemNumber", "Description", "Quantity", "Uom", "UnitRate", "Amount", "Notes"
    };

    public ExportBoqTemplateCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.IncludeColumns)
            .NotEmpty()
            .WithMessage("At least one column must be included.")
            .Must(columns => columns.All(c => AllowedColumns.Contains(c)))
            .WithMessage($"Invalid column name. Allowed columns: {string.Join(", ", AllowedColumns)}");

        RuleFor(x => x.LockColumns)
            .Must(columns => columns.All(c => AllowedColumns.Contains(c)))
            .WithMessage($"Invalid lock column name. Allowed columns: {string.Join(", ", AllowedColumns)}");

        RuleFor(x => x.Language)
            .IsInEnum()
            .WithMessage("Invalid language selection.");
    }
}
