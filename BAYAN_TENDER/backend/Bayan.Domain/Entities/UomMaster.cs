using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a unit of measurement in the master list.
/// </summary>
public class UomMaster : BaseEntity
{
    /// <summary>
    /// UOM code (e.g., "m2", "LM", "sqft").
    /// </summary>
    public string Code { get; set; } = string.Empty;

    /// <summary>
    /// UOM name (e.g., "Square Meter", "Linear Meter").
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Category of the UOM.
    /// </summary>
    public UomCategory Category { get; set; }

    /// <summary>
    /// Base unit code for this category (e.g., "m2" for Area).
    /// </summary>
    public string? BaseUnitCode { get; set; }

    /// <summary>
    /// Conversion factor to convert to base unit.
    /// </summary>
    public decimal? ConversionToBase { get; set; }

    /// <summary>
    /// Whether this is a system-defined UOM.
    /// </summary>
    public bool IsSystem { get; set; } = true;
}
