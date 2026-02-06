using FluentValidation;

namespace Bayan.Application.Features.Clients.Commands.CreateClient;

/// <summary>
/// Validator for the CreateClientCommand.
/// </summary>
public class CreateClientCommandValidator : AbstractValidator<CreateClientCommand>
{
    public CreateClientCommandValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .WithMessage("Client name is required.")
            .MaximumLength(200)
            .WithMessage("Client name must not exceed 200 characters.");

        RuleFor(x => x.ContactPerson)
            .MaximumLength(150)
            .WithMessage("Contact person name must not exceed 150 characters.")
            .When(x => !string.IsNullOrEmpty(x.ContactPerson));

        RuleFor(x => x.Email)
            .EmailAddress()
            .WithMessage("A valid email address is required.")
            .MaximumLength(256)
            .WithMessage("Email must not exceed 256 characters.")
            .When(x => !string.IsNullOrEmpty(x.Email));

        RuleFor(x => x.Phone)
            .MaximumLength(50)
            .WithMessage("Phone number must not exceed 50 characters.")
            .Matches(@"^[\d\s\+\-\(\)]+$")
            .WithMessage("Phone number contains invalid characters.")
            .When(x => !string.IsNullOrEmpty(x.Phone));

        RuleFor(x => x.Address)
            .MaximumLength(500)
            .WithMessage("Address must not exceed 500 characters.")
            .When(x => !string.IsNullOrEmpty(x.Address));
    }
}
