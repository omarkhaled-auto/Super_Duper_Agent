using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.AddBoqItem;

/// <summary>
/// Validator for the AddBoqItemCommand.
/// </summary>
public class AddBoqItemCommandValidator : AbstractValidator<AddBoqItemCommand>
{
    private readonly IApplicationDbContext _context;

    public AddBoqItemCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExistsAsync)
            .WithMessage("Tender not found.");

        RuleFor(x => x.SectionId)
            .NotEmpty()
            .WithMessage("Section ID is required.")
            .MustAsync(SectionExistsAsync)
            .WithMessage("Section not found or does not belong to this tender.");

        RuleFor(x => x.ItemNumber)
            .NotEmpty()
            .WithMessage("Item number is required.")
            .MaximumLength(50)
            .WithMessage("Item number must not exceed 50 characters.")
            .MustAsync(ItemNumberUniqueAsync)
            .WithMessage("Item number already exists for this tender.");

        RuleFor(x => x.Description)
            .NotEmpty()
            .WithMessage("Item description is required.")
            .MaximumLength(2000)
            .WithMessage("Item description must not exceed 2000 characters.");

        RuleFor(x => x.Quantity)
            .GreaterThan(0)
            .WithMessage("Quantity must be greater than 0.");

        RuleFor(x => x.Uom)
            .NotEmpty()
            .WithMessage("Unit of measurement is required.")
            .MaximumLength(20)
            .WithMessage("Unit of measurement must not exceed 20 characters.")
            .MustAsync(UomExistsAsync)
            .WithMessage("Unit of measurement not found in the system.");

        RuleFor(x => x.ItemType)
            .IsInEnum()
            .WithMessage("Invalid item type.");

        RuleFor(x => x.Notes)
            .MaximumLength(1000)
            .WithMessage("Notes must not exceed 1000 characters.")
            .When(x => !string.IsNullOrEmpty(x.Notes));

        RuleFor(x => x.SortOrder)
            .GreaterThanOrEqualTo(0)
            .WithMessage("Sort order must be non-negative.");
    }

    private async Task<bool> TenderExistsAsync(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders
            .AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> SectionExistsAsync(
        AddBoqItemCommand command,
        Guid sectionId,
        CancellationToken cancellationToken)
    {
        return await _context.BoqSections
            .AnyAsync(s => s.Id == sectionId && s.TenderId == command.TenderId, cancellationToken);
    }

    private async Task<bool> ItemNumberUniqueAsync(
        AddBoqItemCommand command,
        string itemNumber,
        CancellationToken cancellationToken)
    {
        return !await _context.BoqItems
            .AnyAsync(i => i.TenderId == command.TenderId && i.ItemNumber == itemNumber, cancellationToken);
    }

    private async Task<bool> UomExistsAsync(string uom, CancellationToken cancellationToken)
    {
        return await _context.UnitsOfMeasure
            .AnyAsync(u => u.Code == uom && u.IsActive, cancellationToken);
    }
}
