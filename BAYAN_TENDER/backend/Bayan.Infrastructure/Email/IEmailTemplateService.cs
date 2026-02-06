namespace Bayan.Infrastructure.Email;

/// <summary>
/// Interface for email template rendering service.
/// </summary>
public interface IEmailTemplateService
{
    /// <summary>
    /// Renders an email template with the provided merge fields.
    /// </summary>
    /// <param name="templateName">The name of the template (without extension).</param>
    /// <param name="mergeFields">Dictionary of field names and values to merge.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A tuple of (subject, htmlBody).</returns>
    Task<(string Subject, string HtmlBody)> RenderTemplateAsync(
        string templateName,
        Dictionary<string, string> mergeFields,
        CancellationToken cancellationToken = default);
}
