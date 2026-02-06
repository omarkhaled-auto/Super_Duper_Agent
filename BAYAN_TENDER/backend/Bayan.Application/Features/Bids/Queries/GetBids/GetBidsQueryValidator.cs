using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Queries.GetBids;

/// <summary>
/// Validator for the GetBidsQuery.
/// </summary>
public class GetBidsQueryValidator : AbstractValidator<GetBidsQuery>
{
    private readonly IApplicationDbContext _context;

    public GetBidsQueryValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.")
            .MustAsync(TenderExists)
            .WithMessage("The specified tender does not exist.");

        RuleFor(x => x.Page)
            .GreaterThan(0)
            .WithMessage("Page number must be greater than 0.");

        RuleFor(x => x.PageSize)
            .InclusiveBetween(1, 100)
            .WithMessage("Page size must be between 1 and 100.");
    }

    private async Task<bool> TenderExists(Guid tenderId, CancellationToken cancellationToken)
    {
        return await _context.Tenders.AnyAsync(t => t.Id == tenderId, cancellationToken);
    }
}
