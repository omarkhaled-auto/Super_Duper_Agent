using Bayan.Application.Common.Interfaces;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bidders.Commands.CreateBidder;

/// <summary>
/// Validator for the CreateBidderCommand.
/// </summary>
public class CreateBidderCommandValidator : AbstractValidator<CreateBidderCommand>
{
    private readonly IApplicationDbContext _context;

    public CreateBidderCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.CompanyName)
            .NotEmpty()
            .WithMessage("Company name is required.")
            .MaximumLength(200)
            .WithMessage("Company name must not exceed 200 characters.");

        RuleFor(x => x.Email)
            .NotEmpty()
            .WithMessage("Email is required.")
            .EmailAddress()
            .WithMessage("A valid email address is required.")
            .MaximumLength(256)
            .WithMessage("Email must not exceed 256 characters.");

        RuleFor(x => x.CRNumber)
            .MaximumLength(50)
            .WithMessage("CR Number must not exceed 50 characters.")
            .MustAsync(BeUniqueCRNumber)
            .WithMessage("A bidder with this CR Number already exists.")
            .When(x => !string.IsNullOrEmpty(x.CRNumber));

        RuleFor(x => x.LicenseNumber)
            .MaximumLength(50)
            .WithMessage("License number must not exceed 50 characters.")
            .When(x => !string.IsNullOrEmpty(x.LicenseNumber));

        RuleFor(x => x.ContactPerson)
            .NotEmpty()
            .WithMessage("Contact person is required.")
            .MaximumLength(150)
            .WithMessage("Contact person name must not exceed 150 characters.");

        RuleFor(x => x.Phone)
            .MaximumLength(50)
            .WithMessage("Phone number must not exceed 50 characters.")
            .Matches(@"^[\d\s\+\-\(\)]+$")
            .WithMessage("Phone number contains invalid characters.")
            .When(x => !string.IsNullOrEmpty(x.Phone));

        RuleFor(x => x.TradeSpecialization)
            .MaximumLength(200)
            .WithMessage("Trade specialization must not exceed 200 characters.")
            .When(x => !string.IsNullOrEmpty(x.TradeSpecialization));
    }

    private async Task<bool> BeUniqueCRNumber(string? crNumber, CancellationToken cancellationToken)
    {
        if (string.IsNullOrEmpty(crNumber))
        {
            return true;
        }

        return !await _context.Bidders
            .AnyAsync(b => b.CRNumber == crNumber, cancellationToken);
    }
}
