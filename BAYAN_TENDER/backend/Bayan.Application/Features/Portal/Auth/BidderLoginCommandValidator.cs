using FluentValidation;

namespace Bayan.Application.Features.Portal.Auth;

/// <summary>
/// Validator for BidderLoginCommand.
/// </summary>
public class BidderLoginCommandValidator : AbstractValidator<BidderLoginCommand>
{
    public BidderLoginCommandValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email is required.")
            .EmailAddress().WithMessage("A valid email address is required.")
            .MaximumLength(256).WithMessage("Email must not exceed 256 characters.");

        RuleFor(x => x.Password)
            .NotEmpty().WithMessage("Password is required.")
            .MinimumLength(1).WithMessage("Password is required.");
    }
}
