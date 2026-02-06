using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Auth.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Auth.Queries.GetCurrentUser;

/// <summary>
/// Handler for GetCurrentUserQuery.
/// </summary>
public class GetCurrentUserQueryHandler : IRequestHandler<GetCurrentUserQuery, UserDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public GetCurrentUserQueryHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<UserDto> Handle(GetCurrentUserQuery request, CancellationToken cancellationToken)
    {
        if (!_currentUserService.IsAuthenticated || !_currentUserService.UserId.HasValue)
        {
            throw new UnauthorizedAccessException("User is not authenticated.");
        }

        var userId = _currentUserService.UserId.Value;

        var user = await _context.Users
            .AsNoTracking()
            .FirstOrDefaultAsync(u => u.Id == userId, cancellationToken);

        if (user == null)
        {
            throw new UnauthorizedAccessException("User not found.");
        }

        if (!user.IsActive)
        {
            throw new UnauthorizedAccessException("User account has been deactivated.");
        }

        return MapToUserDto(user);
    }

    private static UserDto MapToUserDto(User user)
    {
        return new UserDto
        {
            Id = user.Id,
            Email = user.Email,
            FirstName = user.FirstName,
            LastName = user.LastName,
            FullName = user.FullName,
            PhoneNumber = user.PhoneNumber,
            Role = user.Role,
            IsActive = user.IsActive,
            EmailVerified = user.EmailVerified,
            CompanyName = user.CompanyName,
            Department = user.Department,
            JobTitle = user.JobTitle,
            ProfilePictureUrl = user.ProfilePictureUrl,
            PreferredLanguage = user.PreferredLanguage,
            TimeZone = user.TimeZone,
            LastLoginAt = user.LastLoginAt,
            CreatedAt = user.CreatedAt
        };
    }
}
