using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.CancelTender;

/// <summary>
/// Validator for the CancelTenderCommand.
/// </summary>
public class CancelTenderCommandValidator : AbstractValidator<CancelTenderCommand>
{
    private readonly IApplicationDbContext _context;

    public CancelTenderCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.Id)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExists)
            .WithMessage("The specified tender does not exist.")
            .MustAsync(TenderCanBeCancelled)
            .WithMessage("Tender cannot be cancelled. Only Draft, Active, or Evaluation status tenders can be cancelled.");

        RuleFor(x => x.Reason)
            .MaximumLength(2000)
            .WithMessage("Cancellation reason must not exceed 2000 characters.")
            .When(x => !string.IsNullOrEmpty(x.Reason));
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> TenderCanBeCancelled(Guid tenderId, CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == tenderId, cancellationToken);

        if (tender == null)
        {
            return true; // Will be caught by TenderExists rule
        }

        // Can cancel Draft, Active, or Evaluation status tenders
        // Cannot cancel already Cancelled or Awarded tenders
        return tender.Status == TenderStatus.Draft ||
               tender.Status == TenderStatus.Active ||
               tender.Status == TenderStatus.Evaluation;
    }
}
