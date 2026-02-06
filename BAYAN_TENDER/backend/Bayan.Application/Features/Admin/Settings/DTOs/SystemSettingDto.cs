namespace Bayan.Application.Features.Admin.Settings.DTOs;

/// <summary>
/// Data transfer object for system settings.
/// </summary>
public record SystemSettingDto
{
    /// <summary>
    /// Unique identifier for the setting.
    /// </summary>
    public Guid Id { get; init; }

    /// <summary>
    /// Unique key identifier for the setting.
    /// </summary>
    public string Key { get; init; } = string.Empty;

    /// <summary>
    /// Value of the setting.
    /// </summary>
    public string Value { get; init; } = string.Empty;

    /// <summary>
    /// Description of what the setting controls.
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// Data type of the setting value.
    /// </summary>
    public string DataType { get; init; } = "string";

    /// <summary>
    /// Category or group the setting belongs to.
    /// </summary>
    public string? Category { get; init; }

    /// <summary>
    /// Whether this setting can be modified by administrators.
    /// </summary>
    public bool IsEditable { get; init; }

    /// <summary>
    /// Display order for UI presentation.
    /// </summary>
    public int DisplayOrder { get; init; }

    /// <summary>
    /// Timestamp when the setting was last modified.
    /// </summary>
    public DateTime? LastModifiedAt { get; init; }
}
