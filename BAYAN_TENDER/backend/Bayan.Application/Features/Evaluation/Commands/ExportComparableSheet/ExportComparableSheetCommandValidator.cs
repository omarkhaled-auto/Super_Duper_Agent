using FluentValidation;

namespace Bayan.Application.Features.Evaluation.Commands.ExportComparableSheet;

/// <summary>
/// Validator for ExportComparableSheetCommand.
/// </summary>
public class ExportComparableSheetCommandValidator : AbstractValidator<ExportComparableSheetCommand>
{
    public ExportComparableSheetCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");
    }
}
