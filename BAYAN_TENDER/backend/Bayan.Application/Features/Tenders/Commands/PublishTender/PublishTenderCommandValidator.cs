using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.PublishTender;

/// <summary>
/// Validator for the PublishTenderCommand.
/// </summary>
public class PublishTenderCommandValidator : AbstractValidator<PublishTenderCommand>
{
    private readonly IApplicationDbContext _context;

    public PublishTenderCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.Id)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExists)
            .WithMessage("The specified tender does not exist.")
            .MustAsync(TenderIsDraft)
            .WithMessage("Only Draft tenders can be published.")
            .MustAsync(TenderHasValidDeadlines)
            .WithMessage("Tender deadlines must be in the future to publish.")
            .MustAsync(TenderHasEvaluationCriteria)
            .WithMessage("Tender must have at least one evaluation criterion to be published.");
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> TenderIsDraft(Guid tenderId, CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == tenderId, cancellationToken);

        return tender?.Status == TenderStatus.Draft;
    }

    private async Task<bool> TenderHasValidDeadlines(Guid tenderId, CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == tenderId, cancellationToken);

        if (tender == null)
        {
            return true; // Will be caught by TenderExists rule
        }

        var now = DateTime.UtcNow;
        return tender.ClarificationDeadline > now &&
               tender.SubmissionDeadline > now &&
               tender.OpeningDate >= tender.SubmissionDeadline;
    }

    private async Task<bool> TenderHasEvaluationCriteria(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.EvaluationCriteria
            .AnyAsync(c => c.TenderId == tenderId, cancellationToken);
    }
}
