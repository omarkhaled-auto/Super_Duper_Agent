namespace Bayan.Application.Features.Notifications.Queries.GetNotificationPreferences;

using Bayan.Application.Features.Notifications.DTOs;
using MediatR;

/// <summary>
/// Query to retrieve the current user's notification preferences.
/// </summary>
public record GetNotificationPreferencesQuery : IRequest<NotificationPreferencesDto>;
