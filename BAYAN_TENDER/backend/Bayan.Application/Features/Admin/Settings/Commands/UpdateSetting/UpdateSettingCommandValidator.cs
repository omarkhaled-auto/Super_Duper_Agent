namespace Bayan.Application.Features.Admin.Settings.Commands.UpdateSetting;

using FluentValidation;

/// <summary>
/// Validator for UpdateSettingCommand.
/// </summary>
public class UpdateSettingCommandValidator : AbstractValidator<UpdateSettingCommand>
{
    public UpdateSettingCommandValidator()
    {
        RuleFor(x => x.Key)
            .NotEmpty()
            .WithMessage("Setting key is required.")
            .MaximumLength(100)
            .WithMessage("Setting key must not exceed 100 characters.");

        RuleFor(x => x.Value)
            .NotNull()
            .WithMessage("Setting value cannot be null.")
            .MaximumLength(1000)
            .WithMessage("Setting value must not exceed 1000 characters.");
    }
}
