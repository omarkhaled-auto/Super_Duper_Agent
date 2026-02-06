namespace Bayan.Application.Features.Admin.Settings.Queries.GetSettings;

using Bayan.Application.Features.Admin.Settings.DTOs;
using MediatR;

/// <summary>
/// Query to retrieve all system settings.
/// </summary>
public record GetSettingsQuery : IRequest<GetSettingsResponse>
{
    /// <summary>
    /// Optional category filter.
    /// </summary>
    public string? Category { get; init; }
}

/// <summary>
/// Response containing all system settings.
/// </summary>
public record GetSettingsResponse
{
    /// <summary>
    /// List of system settings.
    /// </summary>
    public IReadOnlyList<SystemSettingDto> Settings { get; init; } = Array.Empty<SystemSettingDto>();

    /// <summary>
    /// List of units of measure.
    /// </summary>
    public IReadOnlyList<UnitOfMeasureDto> UnitsOfMeasure { get; init; } = Array.Empty<UnitOfMeasureDto>();
}
