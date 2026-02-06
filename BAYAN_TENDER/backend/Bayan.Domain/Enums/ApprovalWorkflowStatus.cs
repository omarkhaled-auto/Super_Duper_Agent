namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the status of an approval workflow.
/// </summary>
public enum ApprovalWorkflowStatus
{
    /// <summary>
    /// Workflow is pending initiation.
    /// </summary>
    Pending = 0,

    /// <summary>
    /// Workflow is in progress.
    /// </summary>
    InProgress = 1,

    /// <summary>
    /// Workflow has been approved.
    /// </summary>
    Approved = 2,

    /// <summary>
    /// Workflow has been rejected.
    /// </summary>
    Rejected = 3,

    /// <summary>
    /// Workflow returned for revision.
    /// </summary>
    RevisionNeeded = 4
}
