using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using FluentValidation;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Admin.Users.Commands.UpdateUser;

/// <summary>
/// Validator for UpdateUserCommand.
/// </summary>
public class UpdateUserCommandValidator : AbstractValidator<UpdateUserCommand>
{
    private readonly IApplicationDbContext _context;

    public UpdateUserCommandValidator(IApplicationDbContext context)
    {
        _context = context;

        RuleFor(x => x.Id)
            .NotEmpty().WithMessage("User ID is required.");

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

        RuleFor(x => x.PreferredLanguage)
            .MaximumLength(10).WithMessage("Preferred language must not exceed 10 characters.")
            .When(x => !string.IsNullOrEmpty(x.PreferredLanguage));

        RuleFor(x => x.TimeZone)
            .MaximumLength(50).WithMessage("Time zone must not exceed 50 characters.")
            .When(x => !string.IsNullOrEmpty(x.TimeZone));
    }

    private async Task<bool> BeUniqueEmail(UpdateUserCommand command, string email, CancellationToken cancellationToken)
    {
        return !await _context.Users
            .AnyAsync(u => u.Email.ToLower() == email.ToLower() && u.Id != command.Id, cancellationToken);
    }
}
