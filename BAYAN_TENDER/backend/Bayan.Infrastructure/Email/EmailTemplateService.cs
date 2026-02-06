using System.Reflection;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Email;

/// <summary>
/// Email template rendering service that loads HTML templates from embedded resources.
/// </summary>
public partial class EmailTemplateService : IEmailTemplateService
{
    private readonly ILogger<EmailTemplateService> _logger;
    private readonly Dictionary<string, string> _templateCache = new();
    private readonly Dictionary<string, string> _subjectCache = new();

    // Template subjects (can be overridden in templates with <!-- Subject: ... --> comment)
    private static readonly Dictionary<string, string> DefaultSubjects = new()
    {
        { "TenderInvitation", "You have been invited to participate in a tender" },
        { "AddendumNotification", "Addendum Notice: {{TenderTitle}}" },
        { "DeadlineReminder", "Reminder: Submission Deadline Approaching - {{TenderTitle}}" },
        { "UserInvitation", "Welcome to Bayan Tender System" },
        { "PasswordReset", "Password Reset Request" },
        { "BulletinPublished", "Q&A Bulletin {{BulletinNumber}}: {{TenderTitle}}" },
        { "ApprovalRequest", "Approval Required: {{TenderReference}} - {{TenderTitle}}" },
        { "ApprovalDecision", "Approval {{Decision}}: {{TenderReference}} - {{TenderTitle}}" },
        { "AwardNotification", "Tender Awarded: {{TenderReference}} - {{TenderTitle}}" }
    };

    public EmailTemplateService(ILogger<EmailTemplateService> logger)
    {
        _logger = logger;
        LoadTemplates();
    }

    /// <inheritdoc />
    public Task<(string Subject, string HtmlBody)> RenderTemplateAsync(
        string templateName,
        Dictionary<string, string> mergeFields,
        CancellationToken cancellationToken = default)
    {
        if (!_templateCache.TryGetValue(templateName, out var template))
        {
            _logger.LogWarning("Email template '{TemplateName}' not found, using fallback", templateName);
            template = GetFallbackTemplate(templateName);
        }

        // Get subject (either from cache or default)
        var subject = _subjectCache.TryGetValue(templateName, out var cachedSubject)
            ? cachedSubject
            : DefaultSubjects.GetValueOrDefault(templateName, $"Notification: {templateName}");

        // Merge fields into template and subject
        var renderedBody = MergeFields(template, mergeFields);
        var renderedSubject = MergeFields(subject, mergeFields);

        return Task.FromResult((renderedSubject, renderedBody));
    }

    private void LoadTemplates()
    {
        var assembly = Assembly.GetExecutingAssembly();
        var resourceNames = assembly.GetManifestResourceNames()
            .Where(n => n.Contains("Email.Templates") && n.EndsWith(".html"));

        foreach (var resourceName in resourceNames)
        {
            try
            {
                using var stream = assembly.GetManifestResourceStream(resourceName);
                if (stream == null) continue;

                using var reader = new StreamReader(stream);
                var content = reader.ReadToEnd();

                // Extract template name from resource name
                var templateName = ExtractTemplateNameFromResource(resourceName);
                _templateCache[templateName] = content;

                // Extract subject from template if present (<!-- Subject: ... -->)
                var subjectMatch = SubjectRegex().Match(content);
                if (subjectMatch.Success)
                {
                    _subjectCache[templateName] = subjectMatch.Groups[1].Value.Trim();
                }

                _logger.LogDebug("Loaded email template: {TemplateName}", templateName);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to load email template from resource: {ResourceName}", resourceName);
            }
        }

        // If no embedded resources found, load from file system (development fallback)
        if (_templateCache.Count == 0)
        {
            LoadTemplatesFromFileSystem();
        }
    }

    private void LoadTemplatesFromFileSystem()
    {
        var baseDirectory = AppDomain.CurrentDomain.BaseDirectory;
        var templatesPath = Path.Combine(baseDirectory, "Email", "Templates");

        if (!Directory.Exists(templatesPath))
        {
            // Try relative path from assembly location
            var assemblyLocation = Assembly.GetExecutingAssembly().Location;
            var assemblyDirectory = Path.GetDirectoryName(assemblyLocation) ?? baseDirectory;
            templatesPath = Path.Combine(assemblyDirectory, "..", "..", "..", "..",
                "Bayan.Infrastructure", "Email", "Templates");
        }

        if (!Directory.Exists(templatesPath))
        {
            _logger.LogWarning("Email templates directory not found at {Path}", templatesPath);
            return;
        }

        foreach (var file in Directory.GetFiles(templatesPath, "*.html"))
        {
            try
            {
                var templateName = Path.GetFileNameWithoutExtension(file)
                    .Replace("Template", "");
                var content = File.ReadAllText(file);

                _templateCache[templateName] = content;

                // Extract subject from template if present
                var subjectMatch = SubjectRegex().Match(content);
                if (subjectMatch.Success)
                {
                    _subjectCache[templateName] = subjectMatch.Groups[1].Value.Trim();
                }

                _logger.LogDebug("Loaded email template from file: {TemplateName}", templateName);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to load email template from file: {File}", file);
            }
        }
    }

    private static string ExtractTemplateNameFromResource(string resourceName)
    {
        // Resource name format: Bayan.Infrastructure.Email.Templates.TemplateName.html
        var parts = resourceName.Split('.');
        if (parts.Length >= 2)
        {
            return parts[^2].Replace("Template", "");
        }
        return resourceName;
    }

    private static string MergeFields(string template, Dictionary<string, string> mergeFields)
    {
        var result = template;
        foreach (var field in mergeFields)
        {
            result = result.Replace($"{{{{{field.Key}}}}}", field.Value);
        }
        return result;
    }

    private static string GetFallbackTemplate(string templateName)
    {
        return $@"
<!DOCTYPE html>
<html>
<head>
    <meta charset=""utf-8"">
    <title>{templateName}</title>
</head>
<body style=""font-family: Arial, sans-serif; line-height: 1.6; color: #333;"">
    <div style=""max-width: 600px; margin: 0 auto; padding: 20px;"">
        <h1 style=""color: #2563eb;"">Bayan Tender System</h1>
        <p>This is an automated notification from the Bayan Tender System.</p>
        <p>Template: {templateName}</p>
        <hr style=""border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;"">
        <p style=""color: #6b7280; font-size: 12px;"">
            This is an automated message. Please do not reply to this email.
        </p>
    </div>
</body>
</html>";
    }

    [GeneratedRegex(@"<!--\s*Subject:\s*(.+?)\s*-->", RegexOptions.Singleline)]
    private static partial Regex SubjectRegex();
}
