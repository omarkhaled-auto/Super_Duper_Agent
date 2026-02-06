namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the status of an approval level.
/// </summary>
public enum ApprovalLevelStatus
{
    /// <summary>
    /// Waiting for previous level.
    /// </summary>
    Waiting = 0,

    /// <summary>
    /// Currently active for decision.
    /// </summary>
    Active = 1,

    /// <summary>
    /// Level approved.
    /// </summary>
    Approved = 2,

    /// <summary>
    /// Level rejected.
    /// </summary>
    Rejected = 3,

    /// <summary>
    /// Returned for revision.
    /// </summary>
    Returned = 4
}
