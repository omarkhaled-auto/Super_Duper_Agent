using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Admin.Users.Commands.CreateUser;

/// <summary>
/// Validator for CreateUserCommand.
/// </summary>
public class CreateUserCommandValidator : AbstractValidator<CreateUserCommand>
{
    private readonly IApplicationDbContext _context;

    public CreateUserCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.FirstName)
            .NotEmpty().WithMessage("First name is required.")
            .MaximumLength(100).WithMessage("First name must not exceed 100 characters.");

        RuleFor(x => x.LastName)
            .NotEmpty().WithMessage("Last name is required.")
            .MaximumLength(100).WithMessage("Last name must not exceed 100 characters.");

        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email is required.")
            .EmailAddress().WithMessage("A valid email address is required.")
            .MaximumLength(256).WithMessage("Email must not exceed 256 characters.")
            .MustAsync(BeUniqueEmail).WithMessage("A user with this email already exists.");

        RuleFor(x => x.Role)
            .IsInEnum().WithMessage("Invalid role specified.");

        RuleFor(x => x.Phone)
            .MaximumLength(20).WithMessage("Phone number must not exceed 20 characters.")
            .When(x => !string.IsNullOrEmpty(x.Phone));

        RuleFor(x => x.CompanyName)
            .NotEmpty().WithMessage("Company name is required for bidder users.")
            .When(x => x.Role == UserRole.Bidder);

        RuleFor(x => x.CompanyName)
            .MaximumLength(200).WithMessage("Company name must not exceed 200 characters.")
            .When(x => !string.IsNullOrEmpty(x.CompanyName));

        RuleFor(x => x.Department)
            .MaximumLength(100).WithMessage("Department must not exceed 100 characters.")
            .When(x => !string.IsNullOrEmpty(x.Department));

        RuleFor(x => x.JobTitle)
            .MaximumLength(100).WithMessage("Job title must not exceed 100 characters.")
            .When(x => !string.IsNullOrEmpty(x.JobTitle));
    }

    private async Task<bool> BeUniqueEmail(string email, CancellationToken cancellationToken)
    {
        return !await _context.Users
            .AnyAsync(u => u.Email.ToLower() == email.ToLower(), cancellationToken);
    }
}
