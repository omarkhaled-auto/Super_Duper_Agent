using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.UpdateTender;

/// <summary>
/// Validator for the UpdateTenderCommand.
/// </summary>
public class UpdateTenderCommandValidator : AbstractValidator<UpdateTenderCommand>
{
    private readonly IApplicationDbContext _context;

    public UpdateTenderCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.Id)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExists)
            .WithMessage("The specified tender does not exist.");

        RuleFor(x => x.Title)
            .NotEmpty()
            .WithMessage("Tender title is required.")
            .MaximumLength(500)
            .WithMessage("Tender title must not exceed 500 characters.");

        RuleFor(x => x.ClientId)
            .NotEmpty()
            .WithMessage("Client is required.")
            .MustAsync(ClientExists)
            .WithMessage("The specified client does not exist.");

        RuleFor(x => x.BaseCurrency)
            .NotEmpty()
            .WithMessage("Base currency is required.")
            .Length(3)
            .WithMessage("Currency code must be exactly 3 characters (ISO 4217).")
            .Matches("^[A-Z]{3}$")
            .WithMessage("Currency code must be uppercase letters (ISO 4217).")
            .MustAsync(CurrencyNotChangedIfBidsReceived)
            .WithMessage("Currency cannot be changed once bids have been received.");

        RuleFor(x => x.BidValidityDays)
            .GreaterThan(0)
            .WithMessage("Bid validity days must be greater than 0.")
            .LessThanOrEqualTo(365)
            .WithMessage("Bid validity days must not exceed 365 days.");

        RuleFor(x => x.IssueDate)
            .NotEmpty()
            .WithMessage("Issue date is required.");

        RuleFor(x => x.ClarificationDeadline)
            .NotEmpty()
            .WithMessage("Clarification deadline is required.")
            .GreaterThan(x => x.IssueDate)
            .WithMessage("Clarification deadline must be after the issue date.");

        RuleFor(x => x.SubmissionDeadline)
            .NotEmpty()
            .WithMessage("Submission deadline is required.")
            .Must((command, submissionDeadline) =>
                submissionDeadline > command.ClarificationDeadline.AddDays(3))
            .WithMessage("Submission deadline must be at least 3 days after the clarification deadline.");

        RuleFor(x => x.OpeningDate)
            .NotEmpty()
            .WithMessage("Opening date is required.")
            .GreaterThanOrEqualTo(x => x.SubmissionDeadline)
            .WithMessage("Opening date must be on or after the submission deadline.");

        RuleFor(x => x.TechnicalWeight)
            .InclusiveBetween(0, 100)
            .WithMessage("Technical weight must be between 0 and 100.");

        RuleFor(x => x.CommercialWeight)
            .InclusiveBetween(0, 100)
            .WithMessage("Commercial weight must be between 0 and 100.");

        RuleFor(x => x)
            .Must(x => x.TechnicalWeight + x.CommercialWeight == 100)
            .WithMessage("Technical weight and commercial weight must sum to 100.");

        RuleFor(x => x)
            .MustAsync(TenderIsEditable)
            .WithMessage("Tender cannot be edited in its current status. Only Draft tenders can be edited.");

        RuleFor(x => x.EvaluationCriteria)
            .Must(criteria => criteria == null || criteria.Count == 0 ||
                  criteria.Sum(c => c.WeightPercentage) == 100)
            .WithMessage("Evaluation criteria weights must sum to 100 when criteria are provided.");

        RuleForEach(x => x.EvaluationCriteria)
            .ChildRules(criterion =>
            {
                criterion.RuleFor(c => c.Name)
                    .NotEmpty()
                    .WithMessage("Criterion name is required.")
                    .MaximumLength(200)
                    .WithMessage("Criterion name must not exceed 200 characters.");

                criterion.RuleFor(c => c.WeightPercentage)
                    .InclusiveBetween(0, 100)
                    .WithMessage("Criterion weight must be between 0 and 100.");

                criterion.RuleFor(c => c.GuidanceNotes)
                    .MaximumLength(2000)
                    .WithMessage("Guidance notes must not exceed 2000 characters.")
                    .When(c => !string.IsNullOrEmpty(c.GuidanceNotes));

                criterion.RuleFor(c => c.SortOrder)
                    .GreaterThanOrEqualTo(0)
                    .WithMessage("Sort order must be non-negative.");
            });
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }

    private async Task<bool> ClientExists(Guid clientId, CancellationToken cancellationToken)
    {
        return await _context.Clients
            .AnyAsync(c => c.Id == clientId && c.IsActive, cancellationToken);
    }

    private async Task<bool> CurrencyNotChangedIfBidsReceived(
        UpdateTenderCommand command,
        string newCurrency,
        CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .Include(t => t.BidSubmissions)
            .FirstOrDefaultAsync(t => t.Id == command.Id, cancellationToken);

        if (tender == null)
        {
            return true; // Will be caught by TenderExists rule
        }

        // If no bids received, currency can be changed
        if (!tender.BidSubmissions.Any())
        {
            return true;
        }

        // If bids received, currency must remain the same
        return tender.BaseCurrency == newCurrency;
    }

    private async Task<bool> TenderIsEditable(
        UpdateTenderCommand command,
        CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == command.Id, cancellationToken);

        if (tender == null)
        {
            return true; // Will be caught by TenderExists rule
        }

        // Only Draft tenders can be fully edited
        return tender.Status == TenderStatus.Draft;
    }
}
