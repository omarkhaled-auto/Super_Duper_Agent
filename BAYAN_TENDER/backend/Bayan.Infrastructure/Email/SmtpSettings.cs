namespace Bayan.Infrastructure.Email;

/// <summary>
/// SMTP configuration settings.
/// </summary>
public class SmtpSettings
{
    /// <summary>
    /// Configuration section name.
    /// </summary>
    public const string SectionName = "SmtpSettings";

    /// <summary>
    /// SMTP server host.
    /// </summary>
    public string Host { get; set; } = "localhost";

    /// <summary>
    /// SMTP server port.
    /// </summary>
    public int Port { get; set; } = 1025;

    /// <summary>
    /// Whether to use SSL/TLS.
    /// </summary>
    public bool UseSsl { get; set; } = false;

    /// <summary>
    /// SMTP username for authentication.
    /// </summary>
    public string? Username { get; set; }

    /// <summary>
    /// SMTP password for authentication.
    /// </summary>
    public string? Password { get; set; }

    /// <summary>
    /// Sender email address.
    /// </summary>
    public string FromEmail { get; set; } = "noreply@bayan-tender.com";

    /// <summary>
    /// Sender display name.
    /// </summary>
    public string FromName { get; set; } = "Bayan Tender System";

    /// <summary>
    /// Connection timeout in seconds.
    /// </summary>
    public int TimeoutSeconds { get; set; } = 30;

    /// <summary>
    /// Whether to enable email sending (useful for dev environments).
    /// </summary>
    public bool EnableSending { get; set; } = true;

    /// <summary>
    /// Base URL for the portal (used in email templates).
    /// </summary>
    public string PortalBaseUrl { get; set; } = "http://localhost:3000";
}
