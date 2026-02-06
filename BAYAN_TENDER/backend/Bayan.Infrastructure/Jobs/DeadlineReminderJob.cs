using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Jobs;

/// <summary>
/// Background job to send deadline reminders for tenders.
/// Sends reminders 3 days and 1 day before submission deadline.
/// </summary>
public class DeadlineReminderJob
{
    private readonly IApplicationDbContext _context;
    private readonly IEmailService _emailService;
    private readonly ILogger<DeadlineReminderJob> _logger;

    public DeadlineReminderJob(
        IApplicationDbContext context,
        IEmailService emailService,
        ILogger<DeadlineReminderJob> logger)
    {
        _context = context;
        _emailService = emailService;
        _logger = logger;
    }

    /// <summary>
    /// Executes the deadline reminder job.
    /// </summary>
    public async Task ExecuteAsync()
    {
        _logger.LogInformation("Starting deadline reminder job at {Time}", DateTime.UtcNow);

        try
        {
            var now = DateTime.UtcNow;
            var threeDaysFromNow = now.AddDays(3).Date;
            var oneDayFromNow = now.AddDays(1).Date;

            // Get tenders with upcoming deadlines
            var tendersWithUpcomingDeadlines = await _context.Tenders
                .AsNoTracking()
                .Include(t => t.TenderBidders)
                    .ThenInclude(tb => tb.Bidder)
                .Where(t => t.Status == TenderStatus.Active)
                .Where(t => t.SubmissionDeadline.Date == threeDaysFromNow ||
                           t.SubmissionDeadline.Date == oneDayFromNow)
                .ToListAsync();

            _logger.LogInformation("Found {Count} tenders with upcoming deadlines", tendersWithUpcomingDeadlines.Count);

            var emailsSent = 0;
            var errors = 0;

            foreach (var tender in tendersWithUpcomingDeadlines)
            {
                var daysUntilDeadline = (tender.SubmissionDeadline.Date - now.Date).Days;
                var reminderType = daysUntilDeadline switch
                {
                    3 => "3-day",
                    1 => "1-day",
                    _ => "final"
                };

                _logger.LogDebug(
                    "Processing {ReminderType} reminder for tender {Reference}",
                    reminderType,
                    tender.Reference);

                // Get bidders who haven't submitted yet
                var biddersToNotify = tender.TenderBidders
                    .Where(tb => tb.QualificationStatus == QualificationStatus.Qualified ||
                                tb.QualificationStatus == QualificationStatus.Pending)
                    .Select(tb => tb.Bidder)
                    .Where(b => b.IsActive && !string.IsNullOrEmpty(b.Email))
                    .ToList();

                foreach (var bidder in biddersToNotify)
                {
                    try
                    {
                        var subject = $"[{reminderType.ToUpper()} REMINDER] Tender Deadline: {tender.Reference}";
                        var body = GenerateReminderEmailBody(
                            bidder.ContactPerson,
                            tender.Title,
                            tender.Reference,
                            tender.SubmissionDeadline,
                            daysUntilDeadline);

                        await _emailService.SendEmailAsync(
                            bidder.Email,
                            subject,
                            body);

                        emailsSent++;

                        _logger.LogDebug(
                            "Sent {ReminderType} reminder to {Email} for tender {Reference}",
                            reminderType,
                            bidder.Email,
                            tender.Reference);
                    }
                    catch (Exception ex)
                    {
                        errors++;
                        _logger.LogError(
                            ex,
                            "Failed to send reminder to {Email} for tender {Reference}",
                            bidder.Email,
                            tender.Reference);
                    }
                }
            }

            _logger.LogInformation(
                "Deadline reminder job completed. Emails sent: {Sent}, Errors: {Errors}",
                emailsSent,
                errors);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error executing deadline reminder job");
            throw;
        }
    }

    private static string GenerateReminderEmailBody(
        string contactPerson,
        string tenderTitle,
        string tenderReference,
        DateTime deadline,
        int daysRemaining)
    {
        var urgencyText = daysRemaining switch
        {
            1 => "<strong style='color: #e74c3c;'>FINAL REMINDER - Deadline is TOMORROW!</strong>",
            3 => "<strong style='color: #f39c12;'>IMPORTANT REMINDER - 3 days remaining</strong>",
            _ => "<strong>Deadline Reminder</strong>"
        };

        return $@"
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1976D2, #1565C0); color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .deadline-box {{ background: #fff; border-left: 4px solid #e74c3c; padding: 15px; margin: 15px 0; }}
        .button {{ display: inline-block; background: #1976D2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
        .footer {{ padding: 15px; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>Tender Deadline Reminder</h1>
        </div>
        <div class='content'>
            <p>Dear {contactPerson},</p>

            <p>{urgencyText}</p>

            <div class='deadline-box'>
                <p><strong>Tender:</strong> {tenderTitle}</p>
                <p><strong>Reference:</strong> {tenderReference}</p>
                <p><strong>Submission Deadline:</strong> {deadline:dddd, MMMM d, yyyy 'at' h:mm tt}</p>
                <p><strong>Days Remaining:</strong> {daysRemaining} day(s)</p>
            </div>

            <p>Please ensure you submit your bid before the deadline. Late submissions will not be accepted.</p>

            <p>If you have any questions or need clarification, please contact us through the bidder portal.</p>

            <p>Best regards,<br/>Bayan Tender Management System</p>
        </div>
        <div class='footer'>
            <p>This is an automated message. Please do not reply directly to this email.</p>
        </div>
    </div>
</body>
</html>";
    }
}
