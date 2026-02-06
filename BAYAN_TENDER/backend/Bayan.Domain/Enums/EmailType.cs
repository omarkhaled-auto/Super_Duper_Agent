namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the type of email notification.
/// </summary>
public enum EmailType
{
    /// <summary>
    /// Tender invitation email.
    /// </summary>
    TenderInvitation = 0,

    /// <summary>
    /// Addendum notice email.
    /// </summary>
    AddendumNotice = 1,

    /// <summary>
    /// Clarification bulletin email.
    /// </summary>
    ClarificationBulletin = 2,

    /// <summary>
    /// Deadline reminder email.
    /// </summary>
    DeadlineReminder = 3,

    /// <summary>
    /// Bid receipt confirmation email.
    /// </summary>
    BidReceipt = 4,

    /// <summary>
    /// Approval request email.
    /// </summary>
    ApprovalRequest = 5
}
