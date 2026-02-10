namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Represents an email attachment.
/// </summary>
public class EmailAttachment
{
    /// <summary>
    /// File name of the attachment.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Content of the attachment as bytes.
    /// </summary>
    public byte[] Content { get; set; } = Array.Empty<byte>();

    /// <summary>
    /// MIME type of the attachment.
    /// </summary>
    public string ContentType { get; set; } = "application/octet-stream";
}

/// <summary>
/// Interface for email service operations.
/// </summary>
public interface IEmailService
{
    /// <summary>
    /// Sends a user invitation email with temporary password.
    /// </summary>
    /// <param name="email">The recipient's email address.</param>
    /// <param name="firstName">The user's first name.</param>
    /// <param name="temporaryPassword">The temporary password for the user.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendUserInvitationEmailAsync(
        string email,
        string firstName,
        string temporaryPassword,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Sends a password reset email with reset token.
    /// </summary>
    /// <param name="email">The recipient's email address.</param>
    /// <param name="firstName">The user's first name.</param>
    /// <param name="resetToken">The password reset token.</param>
    /// <param name="resetUrl">The URL for the password reset page.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendPasswordResetEmailAsync(
        string email,
        string firstName,
        string resetToken,
        string resetUrl,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Sends an email with the specified parameters.
    /// </summary>
    /// <param name="to">The recipient's email address.</param>
    /// <param name="subject">The email subject.</param>
    /// <param name="htmlBody">The HTML body content.</param>
    /// <param name="attachments">Optional attachments.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendEmailAsync(
        string to,
        string subject,
        string htmlBody,
        IEnumerable<EmailAttachment>? attachments = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Sends a templated email with merge fields.
    /// </summary>
    /// <param name="to">The recipient's email address.</param>
    /// <param name="templateName">The name of the template to use.</param>
    /// <param name="mergeFields">Dictionary of field names and values to merge into the template.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendTemplatedEmailAsync(
        string to,
        string templateName,
        Dictionary<string, string> mergeFields,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Sends a tender invitation email to a bidder.
    /// </summary>
    /// <param name="email">The bidder's email address.</param>
    /// <param name="contactPerson">The bidder's contact person name.</param>
    /// <param name="tenderTitle">The tender title.</param>
    /// <param name="tenderReference">The tender reference number.</param>
    /// <param name="submissionDeadline">The submission deadline.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendTenderInvitationEmailAsync(
        string email,
        string contactPerson,
        string tenderTitle,
        string tenderReference,
        DateTime submissionDeadline,
        string? activationToken = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Sends an approval request email to an approver.
    /// </summary>
    /// <param name="email">The approver's email address.</param>
    /// <param name="firstName">The approver's first name.</param>
    /// <param name="tenderTitle">The tender title.</param>
    /// <param name="tenderReference">The tender reference number.</param>
    /// <param name="initiatorName">Name of the user who initiated the approval.</param>
    /// <param name="levelNumber">The approval level number (1, 2, or 3).</param>
    /// <param name="deadline">Optional deadline for the approval.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendApprovalRequestEmailAsync(
        string email,
        string firstName,
        string tenderTitle,
        string tenderReference,
        string initiatorName,
        int levelNumber,
        DateTime? deadline,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Sends an approval decision notification email.
    /// </summary>
    /// <param name="email">The recipient's email address.</param>
    /// <param name="firstName">The recipient's first name.</param>
    /// <param name="tenderTitle">The tender title.</param>
    /// <param name="tenderReference">The tender reference number.</param>
    /// <param name="decision">The decision made (Approved, Rejected, Returned for Revision).</param>
    /// <param name="levelNumber">The approval level number where decision was made.</param>
    /// <param name="comment">Optional comment from the approver.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendApprovalDecisionEmailAsync(
        string email,
        string firstName,
        string tenderTitle,
        string tenderReference,
        string decision,
        int levelNumber,
        string? comment,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Sends an award notification email when a tender is fully approved.
    /// </summary>
    /// <param name="email">The recipient's email address.</param>
    /// <param name="firstName">The recipient's first name.</param>
    /// <param name="tenderTitle">The tender title.</param>
    /// <param name="tenderReference">The tender reference number.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendAwardNotificationEmailAsync(
        string email,
        string firstName,
        string tenderTitle,
        string tenderReference,
        CancellationToken cancellationToken = default);
}
