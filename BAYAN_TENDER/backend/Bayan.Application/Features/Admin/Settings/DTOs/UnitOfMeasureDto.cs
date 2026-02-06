namespace Bayan.Application.Features.Admin.Settings.DTOs;

/// <summary>
/// Data transfer object for units of measure.
/// </summary>
public record UnitOfMeasureDto
{
    /// <summary>
    /// Unique identifier for the unit.
    /// </summary>
    public Guid Id { get; init; }

    /// <summary>
    /// Short code for the unit (e.g., "m2", "kg", "LS").
    /// </summary>
    public string Code { get; init; } = string.Empty;

    /// <summary>
    /// Full name of the unit.
    /// </summary>
    public string Name { get; init; } = string.Empty;

    /// <summary>
    /// Category of the unit (Area, Volume, Length, Weight, etc.).
    /// </summary>
    public string Category { get; init; } = string.Empty;

    /// <summary>
    /// Description of the unit.
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// Conversion factor to the base unit in its category.
    /// </summary>
    public decimal ConversionFactor { get; init; }

    /// <summary>
    /// The base unit code this converts to.
    /// </summary>
    public string? BaseUnitCode { get; init; }

    /// <summary>
    /// Whether this unit is active and available for selection.
    /// </summary>
    public bool IsActive { get; init; }

    /// <summary>
    /// Display order for UI presentation.
    /// </summary>
    public int DisplayOrder { get; init; }
}
