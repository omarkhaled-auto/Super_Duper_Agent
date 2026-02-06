namespace Bayan.Application.Features.Admin.Settings.Commands.UpdateSetting;

using Bayan.Application.Features.Admin.Settings.DTOs;
using MediatR;

/// <summary>
/// Command to update a system setting by key.
/// </summary>
public record UpdateSettingCommand : IRequest<UpdateSettingResponse>
{
    /// <summary>
    /// The key of the setting to update.
    /// </summary>
    public string Key { get; init; } = string.Empty;

    /// <summary>
    /// The new value for the setting.
    /// </summary>
    public string Value { get; init; } = string.Empty;
}

/// <summary>
/// Response after updating a system setting.
/// </summary>
public record UpdateSettingResponse
{
    /// <summary>
    /// Whether the update was successful.
    /// </summary>
    public bool Success { get; init; }

    /// <summary>
    /// The updated setting data.
    /// </summary>
    public SystemSettingDto? Setting { get; init; }

    /// <summary>
    /// Error message if the update failed.
    /// </summary>
    public string? ErrorMessage { get; init; }
}
