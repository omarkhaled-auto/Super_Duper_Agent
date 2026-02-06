namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// Data transfer object for unit of measurement (simplified for BOQ).
/// </summary>
public class UomDto
{
    /// <summary>
    /// Unique identifier for the unit.
    /// </summary>
    public Guid Id { get; set; }

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
}
