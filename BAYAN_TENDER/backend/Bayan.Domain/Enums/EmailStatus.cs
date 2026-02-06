namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the status of an email.
/// </summary>
public enum EmailStatus
{
    /// <summary>
    /// Email is pending to be sent.
    /// </summary>
    Pending = 0,

    /// <summary>
    /// Email has been sent.
    /// </summary>
    Sent = 1,

    /// <summary>
    /// Email sending failed.
    /// </summary>
    Failed = 2,

    /// <summary>
    /// Email bounced.
    /// </summary>
    Bounced = 3
}
