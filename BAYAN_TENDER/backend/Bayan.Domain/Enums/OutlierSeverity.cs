namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the severity of price outliers.
/// </summary>
public enum OutlierSeverity
{
    /// <summary>
    /// Low severity outlier (10-20% deviation).
    /// </summary>
    Low = 0,

    /// <summary>
    /// Medium severity outlier.
    /// </summary>
    Medium = 1,

    /// <summary>
    /// High severity outlier (>20% deviation).
    /// </summary>
    High = 2
}
