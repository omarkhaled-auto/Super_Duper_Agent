using Bayan.Application.Features.Boq.DTOs;
using FluentValidation;

namespace Bayan.Application.Features.Boq.Commands.ValidateBoqImport;

/// <summary>
/// Validator for ValidateBoqImportCommand.
/// </summary>
public class ValidateBoqImportCommandValidator : AbstractValidator<ValidateBoqImportCommand>
{
    public ValidateBoqImportCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.ImportSessionId)
            .NotEmpty()
            .WithMessage("Import session ID is required.");

        RuleFor(x => x.Mappings)
            .NotEmpty()
            .WithMessage("At least one column mapping is required.");

        RuleFor(x => x.Mappings)
            .Must(ContainItemNumberMapping)
            .WithMessage("Item Number column mapping is required.");

        RuleFor(x => x.Mappings)
            .Must(ContainDescriptionMapping)
            .WithMessage("Description column mapping is required.");

        RuleFor(x => x.SheetIndex)
            .GreaterThanOrEqualTo(0)
            .WithMessage("Sheet index must be non-negative.");

        RuleFor(x => x.HeaderRowOverride)
            .GreaterThanOrEqualTo(0)
            .When(x => x.HeaderRowOverride.HasValue)
            .WithMessage("Header row override must be non-negative.");
    }

    private bool ContainItemNumberMapping(List<ColumnMappingDto> mappings)
    {
        return mappings.Any(m => m.BoqField == BoqField.ItemNumber);
    }

    private bool ContainDescriptionMapping(List<ColumnMappingDto> mappings)
    {
        return mappings.Any(m => m.BoqField == BoqField.Description);
    }
}
