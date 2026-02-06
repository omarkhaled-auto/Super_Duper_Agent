namespace Bayan.Domain.Entities;

using Bayan.Domain.Common;

/// <summary>
/// Represents a unit of measure for quantity calculations.
/// </summary>
public class UnitOfMeasure : BaseEntity, IAuditableEntity
{
    /// <summary>
    /// Short code for the unit (e.g., "m2", "kg", "LS").
    /// </summary>
    public string Code { get; set; } = string.Empty;

    /// <summary>
    /// Full name of the unit.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Category of the unit (Area, Volume, Length, Weight, etc.).
    /// </summary>
    public string Category { get; set; } = string.Empty;

    /// <summary>
    /// Description of the unit.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Conversion factor to the base unit in its category.
    /// </summary>
    public decimal ConversionFactor { get; set; } = 1.0m;

    /// <summary>
    /// The base unit code this converts to (null if this is the base unit).
    /// </summary>
    public string? BaseUnitCode { get; set; }

    /// <summary>
    /// Whether this unit is active and available for selection.
    /// </summary>
    public bool IsActive { get; set; } = true;

    /// <summary>
    /// Display order for UI presentation.
    /// </summary>
    public int DisplayOrder { get; set; }

    // IAuditableEntity implementation
    public Guid? CreatedBy { get; set; }
    public Guid? LastModifiedBy { get; set; }
    public DateTime? LastModifiedAt { get; set; }
}
