namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the status of a clarification.
/// </summary>
public enum ClarificationStatus
{
    /// <summary>
    /// Clarification submitted, awaiting review.
    /// </summary>
    Submitted = 0,

    /// <summary>
    /// Clarification is pending response.
    /// </summary>
    Pending = 1,

    /// <summary>
    /// Answer is being drafted.
    /// </summary>
    DraftAnswer = 2,

    /// <summary>
    /// Clarification has been answered.
    /// </summary>
    Answered = 3,

    /// <summary>
    /// Clarification has been published.
    /// </summary>
    Published = 4,

    /// <summary>
    /// Clarification marked as duplicate.
    /// </summary>
    Duplicate = 5,

    /// <summary>
    /// Clarification rejected.
    /// </summary>
    Rejected = 6
}
