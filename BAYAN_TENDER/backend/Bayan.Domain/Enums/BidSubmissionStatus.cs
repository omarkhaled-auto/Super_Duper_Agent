namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the status of a bid submission.
/// </summary>
public enum BidSubmissionStatus
{
    /// <summary>
    /// Bid is being drafted (in-app pricing, not yet submitted).
    /// </summary>
    Draft = -1,

    /// <summary>
    /// Bid has been submitted.
    /// </summary>
    Submitted = 0,

    /// <summary>
    /// Bid has been opened.
    /// </summary>
    Opened = 1,

    /// <summary>
    /// Bid has been imported for analysis.
    /// </summary>
    Imported = 2,

    /// <summary>
    /// Bid has been disqualified.
    /// </summary>
    Disqualified = 3
}
