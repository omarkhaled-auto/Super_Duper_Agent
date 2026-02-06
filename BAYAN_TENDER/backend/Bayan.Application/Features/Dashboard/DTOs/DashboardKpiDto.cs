namespace Bayan.Application.Features.Dashboard.DTOs;

/// <summary>
/// Data transfer object for a single KPI metric.
/// </summary>
public class DashboardKpiDto
{
    /// <summary>
    /// Name/label of the KPI.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Current value of the KPI.
    /// </summary>
    public int Value { get; set; }

    /// <summary>
    /// Icon class name for the KPI (e.g., "pi-file", "pi-clock").
    /// </summary>
    public string Icon { get; set; } = string.Empty;

    /// <summary>
    /// Color theme for the KPI card (e.g., "blue", "green", "orange", "red").
    /// </summary>
    public string Color { get; set; } = string.Empty;

    /// <summary>
    /// Optional change percentage from previous period.
    /// </summary>
    public decimal? Change { get; set; }

    /// <summary>
    /// Whether the change is positive or negative.
    /// </summary>
    public bool? ChangeIsPositive { get; set; }
}
