using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Jobs;

/// <summary>
/// Background job to check for expired NDAs and update their status.
/// Runs daily to flag NDAs that have expired.
/// </summary>
public class NdaExpiryCheckJob
{
    private readonly IApplicationDbContext _context;
    private readonly IEmailService _emailService;
    private readonly ILogger<NdaExpiryCheckJob> _logger;

    public NdaExpiryCheckJob(
        IApplicationDbContext context,
        IEmailService emailService,
        ILogger<NdaExpiryCheckJob> logger)
    {
        _context = context;
        _emailService = emailService;
        _logger = logger;
    }

    /// <summary>
    /// Executes the NDA expiry check job.
    /// </summary>
    public async Task ExecuteAsync()
    {
        _logger.LogInformation("Starting NDA expiry check job at {Time}", DateTime.UtcNow);

        try
        {
            var now = DateTime.UtcNow;
            var warningDate = now.AddDays(7).Date; // Warn 7 days before expiry

            // Find NDAs that have expired
            var expiredNdas = await _context.TenderBidders
                .Include(tb => tb.Bidder)
                .Include(tb => tb.Tender)
                .Where(tb => tb.NdaStatus == NdaStatus.Signed &&
                            tb.NdaExpiryDate.HasValue &&
                            tb.NdaExpiryDate.Value.Date <= now.Date)
                .ToListAsync();

            _logger.LogInformation("Found {Count} expired NDAs", expiredNdas.Count);

            // Update status to Expired
            foreach (var tenderBidder in expiredNdas)
            {
                tenderBidder.NdaStatus = NdaStatus.Expired;
                _logger.LogDebug(
                    "Marked NDA as expired for bidder {BidderId} on tender {TenderId}",
                    tenderBidder.BidderId,
                    tenderBidder.TenderId);
            }

            // Find NDAs expiring soon (warning)
            var expiringNdas = await _context.TenderBidders
                .AsNoTracking()
                .Include(tb => tb.Bidder)
                .Include(tb => tb.Tender)
                .Where(tb => tb.NdaStatus == NdaStatus.Signed &&
                            tb.NdaExpiryDate.HasValue &&
                            tb.NdaExpiryDate.Value.Date > now.Date &&
                            tb.NdaExpiryDate.Value.Date <= warningDate)
                .ToListAsync();

            _logger.LogInformation("Found {Count} NDAs expiring within 7 days", expiringNdas.Count);

            var emailsSent = 0;
            var errors = 0;

            // Send warning emails for expiring NDAs
            foreach (var tenderBidder in expiringNdas)
            {
                if (tenderBidder.Bidder?.Email == null || tenderBidder.Tender == null)
                    continue;

                var daysUntilExpiry = (tenderBidder.NdaExpiryDate!.Value.Date - now.Date).Days;

                try
                {
                    var subject = $"[NDA EXPIRY WARNING] Your NDA for {tenderBidder.Tender.Reference} expires soon";
                    var body = GenerateNdaExpiryWarningEmail(
                        tenderBidder.Bidder.ContactPerson,
                        tenderBidder.Tender.Title,
                        tenderBidder.Tender.Reference,
                        tenderBidder.NdaExpiryDate.Value,
                        daysUntilExpiry);

                    await _emailService.SendEmailAsync(
                        tenderBidder.Bidder.Email,
                        subject,
                        body);

                    emailsSent++;

                    _logger.LogDebug(
                        "Sent NDA expiry warning to {Email} for tender {Reference}",
                        tenderBidder.Bidder.Email,
                        tenderBidder.Tender.Reference);
                }
                catch (Exception ex)
                {
                    errors++;
                    _logger.LogError(
                        ex,
                        "Failed to send NDA expiry warning to {Email}",
                        tenderBidder.Bidder.Email);
                }
            }

            // Send notifications for expired NDAs
            foreach (var tenderBidder in expiredNdas)
            {
                if (tenderBidder.Bidder?.Email == null || tenderBidder.Tender == null)
                    continue;

                try
                {
                    var subject = $"[NDA EXPIRED] Your NDA for {tenderBidder.Tender.Reference} has expired";
                    var body = GenerateNdaExpiredEmail(
                        tenderBidder.Bidder.ContactPerson,
                        tenderBidder.Tender.Title,
                        tenderBidder.Tender.Reference,
                        tenderBidder.NdaExpiryDate!.Value);

                    await _emailService.SendEmailAsync(
                        tenderBidder.Bidder.Email,
                        subject,
                        body);

                    emailsSent++;
                }
                catch (Exception ex)
                {
                    errors++;
                    _logger.LogError(
                        ex,
                        "Failed to send NDA expired notification to {Email}",
                        tenderBidder.Bidder.Email);
                }
            }

            // Save changes
            if (expiredNdas.Any())
            {
                await _context.SaveChangesAsync();
            }

            _logger.LogInformation(
                "NDA expiry check job completed. Expired: {Expired}, Warnings sent: {Warnings}, Errors: {Errors}",
                expiredNdas.Count,
                emailsSent,
                errors);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error executing NDA expiry check job");
            throw;
        }
    }

    private static string GenerateNdaExpiryWarningEmail(
        string contactPerson,
        string tenderTitle,
        string tenderReference,
        DateTime expiryDate,
        int daysRemaining)
    {
        return $@"
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f39c12, #e67e22); color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .warning-box {{ background: #fff; border-left: 4px solid #f39c12; padding: 15px; margin: 15px 0; }}
        .footer {{ padding: 15px; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>NDA Expiry Warning</h1>
        </div>
        <div class='content'>
            <p>Dear {contactPerson},</p>

            <p>This is a reminder that your Non-Disclosure Agreement (NDA) for the following tender is expiring soon:</p>

            <div class='warning-box'>
                <p><strong>Tender:</strong> {tenderTitle}</p>
                <p><strong>Reference:</strong> {tenderReference}</p>
                <p><strong>NDA Expiry Date:</strong> {expiryDate:MMMM d, yyyy}</p>
                <p><strong>Days Until Expiry:</strong> {daysRemaining} day(s)</p>
            </div>

            <p>If you wish to continue participating in this tender, please renew your NDA before the expiry date.</p>

            <p>Contact us if you need assistance with the renewal process.</p>

            <p>Best regards,<br/>Bayan Tender Management System</p>
        </div>
        <div class='footer'>
            <p>This is an automated message. Please do not reply directly to this email.</p>
        </div>
    </div>
</body>
</html>";
    }

    private static string GenerateNdaExpiredEmail(
        string contactPerson,
        string tenderTitle,
        string tenderReference,
        DateTime expiryDate)
    {
        return $@"
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        .expired-box {{ background: #fff; border-left: 4px solid #e74c3c; padding: 15px; margin: 15px 0; }}
        .footer {{ padding: 15px; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>NDA Expired</h1>
        </div>
        <div class='content'>
            <p>Dear {contactPerson},</p>

            <p>Your Non-Disclosure Agreement (NDA) for the following tender has expired:</p>

            <div class='expired-box'>
                <p><strong>Tender:</strong> {tenderTitle}</p>
                <p><strong>Reference:</strong> {tenderReference}</p>
                <p><strong>NDA Expired On:</strong> {expiryDate:MMMM d, yyyy}</p>
            </div>

            <p>Your access to confidential tender documents has been revoked. To regain access, you must sign a new NDA.</p>

            <p>Please contact us if you wish to renew your NDA and continue participating in this tender.</p>

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
