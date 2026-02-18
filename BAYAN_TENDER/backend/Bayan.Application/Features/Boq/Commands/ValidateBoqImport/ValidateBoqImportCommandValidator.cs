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

        // ItemNumber is required UNLESS BillNumber is mapped (bill rows won't have item numbers)
        RuleFor(x => x.Mappings)
            .Must(ContainItemNumberMapping)
            .When(x => !ContainsBillNumberMapping(x.Mappings))
            .WithMessage("Item Number column mapping is required (unless Bill Number is mapped).");

        // Description is required UNLESS BillNumber is mapped (bill rows may only have a bill number)
        RuleFor(x => x.Mappings)
            .Must(ContainDescriptionMapping)
            .When(x => !ContainsBillNumberMapping(x.Mappings))
            .WithMessage("Description column mapping is required (unless Bill Number is mapped).");

        RuleFor(x => x.SheetIndex)
            .GreaterThanOrEqualTo(0)
            .WithMessage("Sheet index must be non-negative.");

        RuleFor(x => x.HeaderRowOverride)
            .GreaterThanOrEqualTo(0)
            .When(x => x.HeaderRowOverride.HasValue)
            .WithMessage("Header row override must be non-negative.");
    }

    private static bool ContainItemNumberMapping(List<ColumnMappingDto> mappings)
    {
        return mappings.Any(m => m.BoqField == BoqField.ItemNumber);
    }

    private static bool ContainDescriptionMapping(List<ColumnMappingDto> mappings)
    {
        return mappings.Any(m => m.BoqField == BoqField.Description);
    }

    private static bool ContainsBillNumberMapping(List<ColumnMappingDto> mappings)
    {
        return mappings != null && mappings.Any(m => m.BoqField == BoqField.BillNumber);
    }
}
