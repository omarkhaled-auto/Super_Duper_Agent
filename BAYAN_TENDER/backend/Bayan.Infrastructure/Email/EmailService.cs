using Bayan.Application.Common.Interfaces;
using MailKit.Net.Smtp;
using MailKit.Security;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MimeKit;

namespace Bayan.Infrastructure.Email;

/// <summary>
/// Email service implementation using MailKit/MimeKit.
/// </summary>
public class EmailService : IEmailService
{
    private readonly SmtpSettings _settings;
    private readonly ILogger<EmailService> _logger;
    private readonly IEmailTemplateService _templateService;

    public EmailService(
        IOptions<SmtpSettings> settings,
        ILogger<EmailService> logger,
        IEmailTemplateService templateService)
    {
        _settings = settings.Value;
        _logger = logger;
        _templateService = templateService;
    }

    /// <inheritdoc />
    public async Task SendEmailAsync(
        string to,
        string subject,
        string htmlBody,
        IEnumerable<EmailAttachment>? attachments = null,
        CancellationToken cancellationToken = default)
    {
        if (!_settings.EnableSending)
        {
            _logger.LogInformation("Email sending is disabled. Would have sent email to {To} with subject '{Subject}'", to, subject);
            return;
        }

        var message = new MimeMessage();
        message.From.Add(new MailboxAddress(_settings.FromName, _settings.FromEmail));
        message.To.Add(MailboxAddress.Parse(to));
        message.Subject = subject;

        var builder = new BodyBuilder
        {
            HtmlBody = htmlBody
        };

        // Add attachments if any
        if (attachments != null)
        {
            foreach (var attachment in attachments)
            {
                builder.Attachments.Add(attachment.FileName, attachment.Content, ContentType.Parse(attachment.ContentType));
            }
        }

        message.Body = builder.ToMessageBody();

        try
        {
            using var client = new SmtpClient();
            client.Timeout = _settings.TimeoutSeconds * 1000;

            var secureSocketOptions = _settings.UseSsl
                ? SecureSocketOptions.StartTls
                : SecureSocketOptions.None;

            await client.ConnectAsync(_settings.Host, _settings.Port, secureSocketOptions, cancellationToken);

            // Authenticate if credentials are provided
            if (!string.IsNullOrEmpty(_settings.Username) && !string.IsNullOrEmpty(_settings.Password))
            {
                await client.AuthenticateAsync(_settings.Username, _settings.Password, cancellationToken);
            }

            await client.SendAsync(message, cancellationToken);
            await client.DisconnectAsync(true, cancellationToken);

            _logger.LogInformation("Email sent successfully to {To} with subject '{Subject}'", to, subject);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to send email to {To} with subject '{Subject}'", to, subject);
            throw;
        }
    }

    /// <inheritdoc />
    public async Task SendTemplatedEmailAsync(
        string to,
        string templateName,
        Dictionary<string, string> mergeFields,
        CancellationToken cancellationToken = default)
    {
        var (subject, htmlBody) = await _templateService.RenderTemplateAsync(templateName, mergeFields, cancellationToken);
        await SendEmailAsync(to, subject, htmlBody, null, cancellationToken);
    }

    /// <inheritdoc />
    public async Task SendUserInvitationEmailAsync(
        string email,
        string firstName,
        string temporaryPassword,
        CancellationToken cancellationToken = default)
    {
        var mergeFields = new Dictionary<string, string>
        {
            { "FirstName", firstName },
            { "TemporaryPassword", temporaryPassword },
            { "PortalLink", _settings.PortalBaseUrl }
        };

        await SendTemplatedEmailAsync(email, "UserInvitation", mergeFields, cancellationToken);
    }

    /// <inheritdoc />
    public async Task SendPasswordResetEmailAsync(
        string email,
        string firstName,
        string resetToken,
        string resetUrl,
        CancellationToken cancellationToken = default)
    {
        var mergeFields = new Dictionary<string, string>
        {
            { "FirstName", firstName },
            { "ResetToken", resetToken },
            { "ResetUrl", resetUrl }
        };

        await SendTemplatedEmailAsync(email, "PasswordReset", mergeFields, cancellationToken);
    }

    /// <inheritdoc />
    public async Task SendTenderInvitationEmailAsync(
        string email,
        string contactPerson,
        string tenderTitle,
        string tenderReference,
        DateTime submissionDeadline,
        CancellationToken cancellationToken = default)
    {
        var mergeFields = new Dictionary<string, string>
        {
            { "BidderName", contactPerson },
            { "TenderTitle", tenderTitle },
            { "TenderReference", tenderReference },
            { "DeadlineDate", submissionDeadline.ToString("dddd, MMMM dd, yyyy 'at' HH:mm 'UTC'") },
            { "PortalLink", _settings.PortalBaseUrl }
        };

        await SendTemplatedEmailAsync(email, "TenderInvitation", mergeFields, cancellationToken);
    }

    /// <inheritdoc />
    public async Task SendApprovalRequestEmailAsync(
        string email,
        string firstName,
        string tenderTitle,
        string tenderReference,
        string initiatorName,
        int levelNumber,
        DateTime? deadline,
        CancellationToken cancellationToken = default)
    {
        var mergeFields = new Dictionary<string, string>
        {
            { "ApproverName", firstName },
            { "TenderTitle", tenderTitle },
            { "TenderReference", tenderReference },
            { "InitiatorName", initiatorName },
            { "LevelNumber", levelNumber.ToString() },
            { "DeadlineDate", deadline?.ToString("dddd, MMMM dd, yyyy 'at' HH:mm 'UTC'") ?? "No deadline set" },
            { "PortalLink", _settings.PortalBaseUrl }
        };

        await SendTemplatedEmailAsync(email, "ApprovalRequest", mergeFields, cancellationToken);
    }

    /// <inheritdoc />
    public async Task SendApprovalDecisionEmailAsync(
        string email,
        string firstName,
        string tenderTitle,
        string tenderReference,
        string decision,
        int levelNumber,
        string? comment,
        CancellationToken cancellationToken = default)
    {
        var mergeFields = new Dictionary<string, string>
        {
            { "RecipientName", firstName },
            { "TenderTitle", tenderTitle },
            { "TenderReference", tenderReference },
            { "Decision", decision },
            { "LevelNumber", levelNumber.ToString() },
            { "Comment", comment ?? "No comment provided" },
            { "PortalLink", _settings.PortalBaseUrl }
        };

        await SendTemplatedEmailAsync(email, "ApprovalDecision", mergeFields, cancellationToken);
    }

    /// <inheritdoc />
    public async Task SendAwardNotificationEmailAsync(
        string email,
        string firstName,
        string tenderTitle,
        string tenderReference,
        CancellationToken cancellationToken = default)
    {
        var mergeFields = new Dictionary<string, string>
        {
            { "RecipientName", firstName },
            { "TenderTitle", tenderTitle },
            { "TenderReference", tenderReference },
            { "PortalLink", _settings.PortalBaseUrl }
        };

        await SendTemplatedEmailAsync(email, "AwardNotification", mergeFields, cancellationToken);
    }
}
