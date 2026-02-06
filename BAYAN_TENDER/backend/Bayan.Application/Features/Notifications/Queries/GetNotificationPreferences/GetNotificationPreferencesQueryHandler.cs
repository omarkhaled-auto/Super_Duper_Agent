namespace Bayan.Application.Features.Notifications.Queries.GetNotificationPreferences;

using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Notifications.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

/// <summary>
/// Handler for retrieving the current user's notification preferences.
/// </summary>
public class GetNotificationPreferencesQueryHandler : IRequestHandler<GetNotificationPreferencesQuery, NotificationPreferencesDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public GetNotificationPreferencesQueryHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<NotificationPreferencesDto> Handle(GetNotificationPreferencesQuery request, CancellationToken cancellationToken)
    {
        var userId = _currentUserService.UserId;

        if (!userId.HasValue)
        {
            throw new UnauthorizedAccessException("User is not authenticated.");
        }

        var preferences = await _context.NotificationPreferences
            .FirstOrDefaultAsync(p => p.UserId == userId.Value, cancellationToken);

        // If no preferences exist, create default ones
        if (preferences == null)
        {
            preferences = new NotificationPreference
            {
                Id = Guid.NewGuid(),
                UserId = userId.Value,
                TenderInvitation = true,
                AddendumIssued = true,
                ClarificationPublished = true,
                DeadlineReminder3Days = true,
                DeadlineReminder1Day = true,
                ApprovalRequest = true
            };

            _context.NotificationPreferences.Add(preferences);
            await _context.SaveChangesAsync(cancellationToken);
        }

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
