using FluentValidation;

namespace Bayan.Application.Features.Boq.Commands.ExecuteBoqImport;

/// <summary>
/// Validator for ExecuteBoqImportCommand.
/// </summary>
public class ExecuteBoqImportCommandValidator : AbstractValidator<ExecuteBoqImportCommand>
{
    public ExecuteBoqImportCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.ImportSessionId)
            .NotEmpty()
            .WithMessage("Import session ID is required.");

        RuleFor(x => x.DefaultSectionTitle)
            .MaximumLength(500)
            .When(x => !string.IsNullOrEmpty(x.DefaultSectionTitle))
            .WithMessage("Default section title cannot exceed 500 characters.");
    }
}
