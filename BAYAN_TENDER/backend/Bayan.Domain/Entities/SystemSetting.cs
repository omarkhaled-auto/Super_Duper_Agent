namespace Bayan.Domain.Entities;

using Bayan.Domain.Common;

/// <summary>
/// Represents a system-wide configuration setting.
/// </summary>
public class SystemSetting : BaseEntity, IAuditableEntity
{
    /// <summary>
    /// Unique key identifier for the setting.
    /// </summary>
    public string Key { get; set; } = string.Empty;

    /// <summary>
    /// Value of the setting.
    /// </summary>
    public string Value { get; set; } = string.Empty;

    /// <summary>
    /// Description of what the setting controls.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Data type of the setting value (string, int, bool, etc.).
    /// </summary>
    public string DataType { get; set; } = "string";

    /// <summary>
    /// Category or group the setting belongs to.
    /// </summary>
    public string? Category { get; set; }

    /// <summary>
    /// Whether this setting can be modified by administrators.
    /// </summary>
    public bool IsEditable { get; set; } = true;

    /// <summary>
    /// Display order for UI presentation.
    /// </summary>
    public int DisplayOrder { get; set; }

    // IAuditableEntity implementation
    public Guid? CreatedBy { get; set; }
    public Guid? LastModifiedBy { get; set; }
    public DateTime? LastModifiedAt { get; set; }
}
