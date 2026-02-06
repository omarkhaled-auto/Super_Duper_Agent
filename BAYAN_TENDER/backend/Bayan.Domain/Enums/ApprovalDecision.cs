namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the decision types for approval levels.
/// </summary>
public enum ApprovalDecision
{
    /// <summary>
    /// Approve the request.
    /// </summary>
    Approve = 0,

    /// <summary>
    /// Reject the request.
    /// </summary>
    Reject = 1,

    /// <summary>
    /// Return for revision.
    /// </summary>
    ReturnForRevision = 2
}
