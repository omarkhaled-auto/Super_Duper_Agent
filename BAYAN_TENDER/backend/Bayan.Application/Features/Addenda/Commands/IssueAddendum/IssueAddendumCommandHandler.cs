using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Addenda.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Addenda.Commands.IssueAddendum;

/// <summary>
/// Handler for the IssueAddendumCommand.
/// </summary>
public class IssueAddendumCommandHandler : IRequestHandler<IssueAddendumCommand, AddendumDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly IEmailService _emailService;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<IssueAddendumCommandHandler> _logger;

    public IssueAddendumCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        IEmailService emailService,
        ICurrentUserService currentUserService,
        ILogger<IssueAddendumCommandHandler> logger)
    {
        _context = context;
        _mapper = mapper;
        _emailService = emailService;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<AddendumDto> Handle(
        IssueAddendumCommand request,
        CancellationToken cancellationToken)
    {
        // Get the addendum with tender details
        var addendum = await _context.Addenda
            .Include(a => a.Tender)
            .FirstOrDefaultAsync(a => a.Id == request.AddendumId && a.TenderId == request.TenderId,
                cancellationToken);

        if (addendum == null)
        {
            throw new NotFoundException("Addendum", request.AddendumId);
        }

        // Ensure addendum is in draft status
        if (addendum.Status != AddendumStatus.Draft)
        {
            throw new InvalidOperationException(
                $"Cannot issue addendum in '{addendum.Status}' status. Addendum must be in Draft status.");
        }

        // Update addendum status
        addendum.Status = AddendumStatus.Issued;
        addendum.IssuedAt = DateTime.UtcNow;
        addendum.IssuedBy = _currentUserService.UserId;
        addendum.IssueDate = DateTime.UtcNow;
        addendum.UpdatedAt = DateTime.UtcNow;

        // If deadline is extended, update the tender's submission deadline
        if (addendum.ExtendsDeadline && addendum.NewDeadline.HasValue)
        {
            addendum.Tender.SubmissionDeadline = addendum.NewDeadline.Value;
            addendum.Tender.LastModifiedAt = DateTime.UtcNow;
            addendum.Tender.LastModifiedBy = _currentUserService.UserId;

            _logger.LogInformation(
                "Tender {TenderId} submission deadline extended to {NewDeadline} via Addendum #{AddendumNumber}",
                addendum.TenderId, addendum.NewDeadline, addendum.AddendumNumber);
        }

        // Get all qualified bidders for this tender
        var qualifiedBidders = await _context.TenderBidders
            .Include(tb => tb.Bidder)
            .Where(tb => tb.TenderId == request.TenderId &&
                         tb.QualificationStatus == QualificationStatus.Qualified)
            .ToListAsync(cancellationToken);

        // Create acknowledgment records for each bidder
        var acknowledgments = new List<AddendumAcknowledgment>();
        foreach (var tenderBidder in qualifiedBidders)
        {
            var acknowledgment = new AddendumAcknowledgment
            {
                Id = Guid.NewGuid(),
                AddendumId = addendum.Id,
                BidderId = tenderBidder.BidderId,
                CreatedAt = DateTime.UtcNow
            };
            acknowledgments.Add(acknowledgment);
        }

        _context.AddendumAcknowledgments.AddRange(acknowledgments);
        await _context.SaveChangesAsync(cancellationToken);

        // Send notification emails to all qualified bidders
        foreach (var tenderBidder in qualifiedBidders)
        {
            try
            {
                var mergeFields = new Dictionary<string, string>
                {
                    { "BidderName", tenderBidder.Bidder.ContactPerson },
                    { "TenderTitle", addendum.Tender.Title },
                    { "TenderReference", addendum.Tender.Reference },
                    { "AddendumNumber", addendum.AddendumNumber.ToString() },
                    { "IssueDate", addendum.IssueDate.ToString("MMMM dd, yyyy") },
                    { "AddendumSummary", addendum.Summary },
                    { "DeadlineExtended", addendum.ExtendsDeadline ? "true" : "" },
                    { "NewDeadline", addendum.NewDeadline?.ToString("dddd, MMMM dd, yyyy 'at' HH:mm 'UTC'") ?? "" },
                    { "PortalLink", "" } // Will be filled by template service
                };

                await _emailService.SendTemplatedEmailAsync(
                    tenderBidder.Bidder.Email,
                    "AddendumNotification",
                    mergeFields,
                    cancellationToken);

                // Update acknowledgment with email sent timestamp
                var ack = acknowledgments.First(a => a.BidderId == tenderBidder.BidderId);
                ack.EmailSentAt = DateTime.UtcNow;

                // Log email in EmailLog
                var emailLog = new EmailLog
                {
                    Id = Guid.NewGuid(),
                    TenderId = addendum.TenderId,
                    RecipientEmail = tenderBidder.Bidder.Email,
                    RecipientName = tenderBidder.Bidder.ContactPerson,
                    EmailType = EmailType.AddendumNotice,
                    Subject = $"Addendum Notice #{addendum.AddendumNumber}: {addendum.Tender.Title}",
                    Body = addendum.Summary,
                    Status = EmailStatus.Sent,
                    SentAt = DateTime.UtcNow,
                    CreatedAt = DateTime.UtcNow
                };
                _context.EmailLogs.Add(emailLog);

                _logger.LogInformation(
                    "Addendum notification email sent to {Email} for Addendum #{AddendumNumber}",
                    tenderBidder.Bidder.Email, addendum.AddendumNumber);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex,
                    "Failed to send addendum notification email to {Email} for Addendum #{AddendumNumber}",
                    tenderBidder.Bidder.Email, addendum.AddendumNumber);

                // Log failed email
                var emailLog = new EmailLog
                {
                    Id = Guid.NewGuid(),
                    TenderId = addendum.TenderId,
                    RecipientEmail = tenderBidder.Bidder.Email,
                    RecipientName = tenderBidder.Bidder.ContactPerson,
                    EmailType = EmailType.AddendumNotice,
                    Subject = $"Addendum Notice #{addendum.AddendumNumber}: {addendum.Tender.Title}",
                    Body = addendum.Summary,
                    Status = EmailStatus.Failed,
                    ErrorMessage = ex.Message,
                    CreatedAt = DateTime.UtcNow
                };
                _context.EmailLogs.Add(emailLog);
            }
        }

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Addendum #{AddendumNumber} issued for Tender {TenderId}. Notifications sent to {BidderCount} bidders.",
            addendum.AddendumNumber, addendum.TenderId, qualifiedBidders.Count);

        return _mapper.Map<AddendumDto>(addendum);
    }
}
