namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the category of a unit of measurement.
/// </summary>
public enum UomCategory
{
    /// <summary>
    /// Area measurements (m2, sqft, etc.).
    /// </summary>
    Area = 0,

    /// <summary>
    /// Length measurements (m, ft, etc.).
    /// </summary>
    Length = 1,

    /// <summary>
    /// Volume measurements (m3, cft, etc.).
    /// </summary>
    Volume = 2,

    /// <summary>
    /// Weight measurements (kg, ton, etc.).
    /// </summary>
    Weight = 3,

    /// <summary>
    /// Lump sum items.
    /// </summary>
    Lump = 4,

    /// <summary>
    /// Count/quantity items.
    /// </summary>
    Count = 5
}
