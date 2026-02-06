namespace Bayan.Application.Features.Notifications.Commands.UpdateNotificationPreferences;

using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Notifications.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

/// <summary>
/// Handler for updating the current user's notification preferences.
/// </summary>
public class UpdateNotificationPreferencesCommandHandler : IRequestHandler<UpdateNotificationPreferencesCommand, NotificationPreferencesDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public UpdateNotificationPreferencesCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<NotificationPreferencesDto> Handle(UpdateNotificationPreferencesCommand request, CancellationToken cancellationToken)
    {
        var userId = _currentUserService.UserId;

        if (!userId.HasValue)
        {
            throw new UnauthorizedAccessException("User is not authenticated.");
        }

        var preferences = await _context.NotificationPreferences
            .FirstOrDefaultAsync(p => p.UserId == userId.Value, cancellationToken);

        if (preferences == null)
        {
            // Create new preferences
            preferences = new NotificationPreference
            {
                Id = Guid.NewGuid(),
                UserId = userId.Value,
                TenderInvitation = request.TenderInvitation,
                AddendumIssued = request.AddendumIssued,
                ClarificationPublished = request.ClarificationPublished,
                DeadlineReminder3Days = request.DeadlineReminder3Days,
                DeadlineReminder1Day = request.DeadlineReminder1Day,
                ApprovalRequest = request.ApprovalRequest
            };

            _context.NotificationPreferences.Add(preferences);
        }
        else
        {
            // Update existing preferences
            preferences.TenderInvitation = request.TenderInvitation;
            preferences.AddendumIssued = request.AddendumIssued;
            preferences.ClarificationPublished = request.ClarificationPublished;
            preferences.DeadlineReminder3Days = request.DeadlineReminder3Days;
            preferences.DeadlineReminder1Day = request.DeadlineReminder1Day;
            preferences.ApprovalRequest = request.ApprovalRequest;
        }

        await _context.SaveChangesAsync(cancellationToken);

        return new NotificationPreferencesDto
        {
            Id = preferences.Id,
            UserId = preferences.UserId,
            TenderInvitation = preferences.TenderInvitation,
            AddendumIssued = preferences.AddendumIssued,
            ClarificationPublished = preferences.ClarificationPublished,
            DeadlineReminder3Days = preferences.DeadlineReminder3Days,
            DeadlineReminder1Day = preferences.DeadlineReminder1Day,
            ApprovalRequest = preferences.ApprovalRequest
        };
    }
}
