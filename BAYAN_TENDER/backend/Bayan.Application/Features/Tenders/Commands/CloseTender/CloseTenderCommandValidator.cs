using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.CloseTender;

/// <summary>
/// Validator for the CloseTenderCommand.
/// Only Active tenders can be closed (transitioned to Evaluation).
/// </summary>
public class CloseTenderCommandValidator : AbstractValidator<CloseTenderCommand>
{
    private readonly IApplicationDbContext _context;

    public CloseTenderCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.Id)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExists)
            .WithMessage("The specified tender does not exist.")
            .MustAsync(TenderCanBeClosed)
            .WithMessage("Tender cannot be closed. Only Active tenders can be closed for evaluation.");
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> TenderCanBeClosed(Guid tenderId, CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == tenderId, cancellationToken);

        if (tender == null)
        {
            return true; // Will be caught by TenderExists rule
        }

        // Only Active tenders can be closed
        return tender.Status == TenderStatus.Active;
    }
}
