using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.AddBoqSection;

/// <summary>
/// Validator for the AddBoqSectionCommand.
/// </summary>
public class AddBoqSectionCommandValidator : AbstractValidator<AddBoqSectionCommand>
{
    private readonly IApplicationDbContext _context;

    public AddBoqSectionCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExistsAsync)
            .WithMessage("Tender not found.");

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
            .When(x => x.ParentSectionId.HasValue);
    }

    private async Task<bool> TenderExistsAsync(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders
            .AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> SectionNumberUniqueAsync(
        AddBoqSectionCommand command,
        string sectionNumber,
        CancellationToken cancellationToken)
    {
        return !await _context.BoqSections
            .AnyAsync(s => s.TenderId == command.TenderId && s.SectionNumber == sectionNumber, cancellationToken);
    }

    private async Task<bool> ParentSectionExistsAsync(
        AddBoqSectionCommand command,
        Guid? parentSectionId,
        CancellationToken cancellationToken)
    {
        if (!parentSectionId.HasValue)
            return true;

        return await _context.BoqSections
            .AnyAsync(s => s.Id == parentSectionId.Value && s.TenderId == command.TenderId, cancellationToken);
    }
}
