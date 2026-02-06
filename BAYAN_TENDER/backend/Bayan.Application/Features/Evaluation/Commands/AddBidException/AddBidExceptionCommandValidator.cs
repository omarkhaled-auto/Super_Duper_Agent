using FluentValidation;

namespace Bayan.Application.Features.Evaluation.Commands.AddBidException;

/// <summary>
/// Validator for AddBidExceptionCommand.
/// </summary>
public class AddBidExceptionCommandValidator : AbstractValidator<AddBidExceptionCommand>
{
    public AddBidExceptionCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidderId)
            .NotEmpty()
            .WithMessage("Bidder ID is required.");

        RuleFor(x => x.ExceptionType)
            .IsInEnum()
            .WithMessage("Invalid exception type.");

        RuleFor(x => x.Description)
            .NotEmpty()
            .WithMessage("Description is required.")
            .MaximumLength(2000)
            .WithMessage("Description cannot exceed 2000 characters.");

        RuleFor(x => x.RiskLevel)
            .IsInEnum()
            .WithMessage("Invalid risk level.");

        When(x => x.CostImpact.HasValue, () =>
        {
            RuleFor(x => x.CostImpact!.Value)
                .GreaterThanOrEqualTo(0)
                .WithMessage("Cost impact cannot be negative.");
        });

        When(x => x.TimeImpactDays.HasValue, () =>
        {
            RuleFor(x => x.TimeImpactDays!.Value)
                .GreaterThanOrEqualTo(0)
                .WithMessage("Time impact cannot be negative.");
        });

        When(x => !string.IsNullOrEmpty(x.Mitigation), () =>
        {
            RuleFor(x => x.Mitigation)
                .MaximumLength(2000)
                .WithMessage("Mitigation cannot exceed 2000 characters.");
        });
    }
}
