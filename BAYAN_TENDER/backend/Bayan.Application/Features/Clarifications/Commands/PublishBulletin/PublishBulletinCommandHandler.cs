using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Clarifications.Commands.PublishBulletin;

/// <summary>
/// Handler for the PublishBulletinCommand.
/// </summary>
public class PublishBulletinCommandHandler : IRequestHandler<PublishBulletinCommand, ClarificationBulletinDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IPdfService _pdfService;
    private readonly IFileStorageService _fileStorageService;
    private readonly IEmailService _emailService;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<PublishBulletinCommandHandler> _logger;

    public PublishBulletinCommandHandler(
        IApplicationDbContext context,
        IPdfService pdfService,
        IFileStorageService fileStorageService,
        IEmailService emailService,
        ICurrentUserService currentUserService,
        ILogger<PublishBulletinCommandHandler> logger)
    {
        _context = context;
        _pdfService = pdfService;
        _fileStorageService = fileStorageService;
        _emailService = emailService;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<ClarificationBulletinDto> Handle(
        PublishBulletinCommand request,
        CancellationToken cancellationToken)
    {
        // Get the tender
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        // Get the selected clarifications
        var clarifications = await _context.Clarifications
            .Where(c => c.TenderId == request.TenderId &&
                       request.ClarificationIds.Contains(c.Id))
            .OrderBy(c => c.ReferenceNumber)
            .ToListAsync(cancellationToken);

        if (clarifications.Count != request.ClarificationIds.Count)
        {
            var foundIds = clarifications.Select(c => c.Id).ToHashSet();
            var missingIds = request.ClarificationIds.Where(id => !foundIds.Contains(id)).ToList();
            throw new ValidationException(
                $"The following clarification IDs were not found: {string.Join(", ", missingIds)}");
        }

        // Auto-approve any DraftAnswer clarifications (admin answered but didn't explicitly approve)
        foreach (var c in clarifications.Where(c => c.Status == ClarificationStatus.DraftAnswer))
        {
            c.Status = ClarificationStatus.Answered;
            c.UpdatedAt = DateTime.UtcNow;
        }

        // Validate all clarifications are in Answered status
        var nonAnsweredClarifications = clarifications
            .Where(c => c.Status != ClarificationStatus.Answered)
            .ToList();

        if (nonAnsweredClarifications.Any())
        {
            var invalidRefs = string.Join(", ", nonAnsweredClarifications.Select(c => c.ReferenceNumber));
            throw new InvalidOperationException(
                $"Cannot publish bulletin. The following clarifications are not in 'Answered' status: {invalidRefs}");
        }

        // Get the next bulletin number for this tender
        var lastBulletinNumber = await _context.ClarificationBulletins
            .Where(b => b.TenderId == request.TenderId)
            .MaxAsync(b => (int?)b.BulletinNumber, cancellationToken) ?? 0;

        var newBulletinNumber = lastBulletinNumber + 1;
        var bulletinReference = $"QB-{newBulletinNumber:D3}";

        _logger.LogInformation(
            "Creating bulletin {BulletinReference} for tender {TenderReference} with {Count} clarifications",
            bulletinReference, tender.Reference, clarifications.Count);

        // Create the bulletin entity
        var bulletin = new ClarificationBulletin
        {
            Id = Guid.NewGuid(),
            TenderId = request.TenderId,
            BulletinNumber = newBulletinNumber,
            IssueDate = DateTime.UtcNow,
            Introduction = request.Introduction,
            ClosingNotes = request.ClosingNotes,
            PublishedBy = _currentUserService.UserId ?? Guid.Empty,
            PublishedAt = DateTime.UtcNow,
            CreatedAt = DateTime.UtcNow
        };

        // Generate the PDF
        byte[] pdfBytes;
        try
        {
            pdfBytes = await _pdfService.GenerateBulletinPdfAsync(
                bulletin, tender, clarifications, cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to generate PDF for bulletin {BulletinReference} on tender {TenderId}",
                bulletinReference, request.TenderId);
            throw new InvalidOperationException(
                $"Failed to generate bulletin PDF for '{bulletinReference}'. Please try again later.", ex);
        }

        // Store the PDF in MinIO
        var pdfFileName = $"{tender.Reference}_{bulletinReference}.pdf";
        var storagePath = $"tender-documents/{request.TenderId}/Clarifications";

        string pdfPath;
        try
        {
            using var pdfStream = new MemoryStream(pdfBytes);
            pdfPath = await _fileStorageService.UploadFileAsync(
                pdfStream,
                pdfFileName,
                "application/pdf",
                storagePath,
                cancellationToken);
        }
        catch (IOException ex)
        {
            _logger.LogError(ex, "Failed to upload bulletin PDF {FileName} for tender {TenderId}",
                pdfFileName, request.TenderId);
            throw new InvalidOperationException(
                $"Failed to store bulletin PDF '{pdfFileName}'. Please try again later.", ex);
        }

        bulletin.PdfPath = pdfPath;

        // Save the bulletin
        _context.ClarificationBulletins.Add(bulletin);

        // Update clarification statuses to Published
        foreach (var clarification in clarifications)
        {
            clarification.Status = ClarificationStatus.Published;
            clarification.PublishedInBulletinId = bulletin.Id;
            clarification.PublishedAt = DateTime.UtcNow;
            clarification.UpdatedAt = DateTime.UtcNow;
        }

        await _context.SaveChangesAsync(cancellationToken);

        // Get qualified bidders to send email notifications
        var qualifiedBidders = await _context.TenderBidders
            .Include(tb => tb.Bidder)
            .Where(tb => tb.TenderId == request.TenderId &&
                        tb.QualificationStatus == QualificationStatus.Qualified)
            .ToListAsync(cancellationToken);

        _logger.LogInformation(
            "Sending bulletin {BulletinReference} email to {Count} qualified bidders",
            bulletinReference, qualifiedBidders.Count);

        // Send email with PDF attachment to each bidder
        foreach (var tenderBidder in qualifiedBidders)
        {
            try
            {
                var attachment = new EmailAttachment
                {
                    FileName = pdfFileName,
                    Content = pdfBytes,
                    ContentType = "application/pdf"
                };

                var mergeFields = new Dictionary<string, string>
                {
                    { "BidderName", tenderBidder.Bidder.ContactPerson },
                    { "TenderTitle", tender.Title },
                    { "TenderReference", tender.Reference },
                    { "BulletinNumber", bulletinReference },
                    { "IssueDate", bulletin.IssueDate.ToString("MMMM dd, yyyy") },
                    { "QuestionCount", clarifications.Count.ToString() },
                    { "PortalLink", "" } // Will be filled by template service
                };

                // Get the rendered email content using the fallback HTML with merge fields
                var subject = $"Q&A Bulletin {bulletinReference}: {tender.Title}";
                var htmlBody = await GetBulletinEmailHtmlAsync(mergeFields);

                // Send email with PDF attachment
                await _emailService.SendEmailAsync(
                    tenderBidder.Bidder.Email,
                    subject,
                    htmlBody,
                    new[] { attachment },
                    cancellationToken);

                // Log the email
                var emailLog = new EmailLog
                {
                    Id = Guid.NewGuid(),
                    TenderId = tender.Id,
                    RecipientEmail = tenderBidder.Bidder.Email,
                    RecipientName = tenderBidder.Bidder.ContactPerson,
                    EmailType = EmailType.ClarificationBulletin,
                    Subject = $"Q&A Bulletin {bulletinReference}: {tender.Title}",
                    Body = $"Bulletin with {clarifications.Count} clarifications",
                    Status = EmailStatus.Sent,
                    SentAt = DateTime.UtcNow,
                    CreatedAt = DateTime.UtcNow
                };
                _context.EmailLogs.Add(emailLog);

                _logger.LogInformation(
                    "Bulletin email sent to {Email} for Bulletin {BulletinReference}",
                    tenderBidder.Bidder.Email, bulletinReference);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex,
                    "Failed to send bulletin email to {Email} for Bulletin {BulletinReference}",
                    tenderBidder.Bidder.Email, bulletinReference);

                // Log failed email
                var emailLog = new EmailLog
                {
                    Id = Guid.NewGuid(),
                    TenderId = tender.Id,
                    RecipientEmail = tenderBidder.Bidder.Email,
                    RecipientName = tenderBidder.Bidder.ContactPerson,
                    EmailType = EmailType.ClarificationBulletin,
                    Subject = $"Q&A Bulletin {bulletinReference}: {tender.Title}",
                    Body = $"Bulletin with {clarifications.Count} clarifications",
                    Status = EmailStatus.Failed,
                    ErrorMessage = ex.Message,
                    CreatedAt = DateTime.UtcNow
                };
                _context.EmailLogs.Add(emailLog);
            }
        }

        await _context.SaveChangesAsync(cancellationToken);

        // Get the publisher name
        var publisher = await _context.Users
            .Where(u => u.Id == bulletin.PublishedBy)
            .Select(u => $"{u.FirstName} {u.LastName}")
            .FirstOrDefaultAsync(cancellationToken) ?? "Unknown";

        _logger.LogInformation(
            "Successfully published Bulletin {BulletinReference} for Tender {TenderReference}",
            bulletinReference, tender.Reference);

        return new ClarificationBulletinDto
        {
            Id = bulletin.Id,
            TenderId = bulletin.TenderId,
            BulletinNumber = bulletin.BulletinNumber,
            IssueDate = bulletin.IssueDate,
            Introduction = bulletin.Introduction,
            ClosingNotes = bulletin.ClosingNotes,
            PdfPath = bulletin.PdfPath,
            PublishedBy = bulletin.PublishedBy,
            PublishedByName = publisher,
            PublishedAt = bulletin.PublishedAt,
            QuestionCount = clarifications.Count,
            Questions = clarifications.Select(c => new ClarificationBulletinQuestionDto
            {
                Id = c.Id,
                ReferenceNumber = c.ReferenceNumber,
                Subject = c.Subject,
                Question = c.Question,
                Answer = c.Answer ?? string.Empty,
                RelatedBoqSection = c.RelatedBoqSection,
                AnsweredAt = c.AnsweredAt
            }).ToList()
        };
    }

    private Task<string> GetBulletinEmailHtmlAsync(Dictionary<string, string> mergeFields)
    {
        // Fallback HTML if template service doesn't have the template yet
        var html = $@"
<!DOCTYPE html>
<html>
<head>
    <meta charset=""utf-8"">
    <title>Q&A Bulletin</title>
</head>
<body style=""font-family: Arial, sans-serif; line-height: 1.6; color: #333;"">
    <div style=""max-width: 600px; margin: 0 auto; padding: 20px;"">
        <h1 style=""color: #2563eb;"">Q&A Bulletin Published</h1>
        <p>Dear {mergeFields["BidderName"]},</p>
        <p>A new Q&A Bulletin has been published for the following tender:</p>
        <div style=""background-color: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0;"">
            <p><strong>Tender:</strong> {mergeFields["TenderTitle"]}</p>
            <p><strong>Reference:</strong> {mergeFields["TenderReference"]}</p>
            <p><strong>Bulletin Number:</strong> {mergeFields["BulletinNumber"]}</p>
            <p><strong>Issue Date:</strong> {mergeFields["IssueDate"]}</p>
            <p><strong>Questions Answered:</strong> {mergeFields["QuestionCount"]}</p>
        </div>
        <p>Please find the bulletin PDF attached to this email. Review the clarifications carefully as they form part of the tender documentation.</p>
        <hr style=""border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;"">
        <p style=""color: #6b7280; font-size: 12px;"">
            This is an automated message from the Bayan Tender System. Please do not reply to this email.
        </p>
    </div>
</body>
</html>";

        return Task.FromResult(html);
    }
}
