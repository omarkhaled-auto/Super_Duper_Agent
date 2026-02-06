namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the type of BOQ item matching.
/// </summary>
public enum MatchType
{
    /// <summary>
    /// Exact match with master BOQ.
    /// </summary>
    ExactMatch = 0,

    /// <summary>
    /// Fuzzy match with master BOQ.
    /// </summary>
    FuzzyMatch = 1,

    /// <summary>
    /// Manually matched by user.
    /// </summary>
    ManualMatch = 2,

    /// <summary>
    /// Extra item not in master BOQ.
    /// </summary>
    ExtraItem = 3,

    /// <summary>
    /// No bid submitted for this item.
    /// </summary>
    NoBid = 4
}
