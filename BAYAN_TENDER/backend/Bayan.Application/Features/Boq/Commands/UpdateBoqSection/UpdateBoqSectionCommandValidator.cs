using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.UpdateBoqSection;

/// <summary>
/// Validator for the UpdateBoqSectionCommand.
/// </summary>
public class UpdateBoqSectionCommandValidator : AbstractValidator<UpdateBoqSectionCommand>
{
    private readonly IApplicationDbContext _context;

    public UpdateBoqSectionCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.SectionId)
            .NotEmpty()
            .WithMessage("Section ID is required.");

        RuleFor(x => x.SectionNumber)
            .NotEmpty()
            .WithMessage("Section number is required.")
            .MaximumLength(50)
            .WithMessage("Section number must not exceed 50 characters.")
            .MustAsync(SectionNumberUniqueAsync)
            .WithMessage("Section number already exists for this tender.");

        RuleFor(x => x.Title)
            .NotEmpty()
            .WithMessage("Section title is required.")
            .MaximumLength(500)
            .WithMessage("Section title must not exceed 500 characters.");

        RuleFor(x => x.SortOrder)
            .GreaterThanOrEqualTo(0)
            .WithMessage("Sort order must be non-negative.");

        RuleFor(x => x.ParentSectionId)
            .MustAsync(ParentSectionExistsAsync)
            .WithMessage("Parent section not found.")
            .When(x => x.ParentSectionId.HasValue)
            .Must((cmd, parentId) => parentId != cmd.SectionId)
            .WithMessage("Section cannot be its own parent.")
            .When(x => x.ParentSectionId.HasValue);
    }

    private async Task<bool> SectionNumberUniqueAsync(
        UpdateBoqSectionCommand command,
        string sectionNumber,
        CancellationToken cancellationToken)
    {
        // Allow the section to keep its own number
        return !await _context.BoqSections
            .AnyAsync(s => s.TenderId == command.TenderId
                        && s.SectionNumber == sectionNumber
                        && s.Id != command.SectionId, cancellationToken);
    }

    private async Task<bool> ParentSectionExistsAsync(
        UpdateBoqSectionCommand command,
        Guid? parentSectionId,
        CancellationToken cancellationToken)
    {
        if (!parentSectionId.HasValue)
            return true;

        return await _context.BoqSections
            .AnyAsync(s => s.Id == parentSectionId.Value && s.TenderId == command.TenderId, cancellationToken);
    }
}
