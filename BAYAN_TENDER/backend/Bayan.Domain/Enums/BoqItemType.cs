namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the type of BOQ item.
/// </summary>
public enum BoqItemType
{
    /// <summary>
    /// Base item included in main scope.
    /// </summary>
    Base = 0,

    /// <summary>
    /// Alternate item (optional).
    /// </summary>
    Alternate = 1,

    /// <summary>
    /// Provisional sum item.
    /// </summary>
    ProvisionalSum = 2,

    /// <summary>
    /// Daywork item.
    /// </summary>
    Daywork = 3
}
