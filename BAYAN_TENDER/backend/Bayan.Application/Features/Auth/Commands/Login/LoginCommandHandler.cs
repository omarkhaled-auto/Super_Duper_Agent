using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Auth.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;
using RefreshTokenEntity = Bayan.Domain.Entities.RefreshToken;

namespace Bayan.Application.Features.Auth.Commands.Login;

/// <summary>
/// Handler for LoginCommand.
/// </summary>
public class LoginCommandHandler : IRequestHandler<LoginCommand, LoginResponseDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtTokenService _jwtTokenService;

    public LoginCommandHandler(
        IApplicationDbContext context,
        IPasswordHasher passwordHasher,
        IJwtTokenService jwtTokenService)
    {
        _context = context;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
    }

    public async Task<LoginResponseDto> Handle(LoginCommand request, CancellationToken cancellationToken)
    {
        // Find user by email
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Email.ToLower() == request.Email.ToLower(), cancellationToken);

        if (user == null)
        {
            throw new UnauthorizedAccessException("Invalid email or password.");
        }

        // Check if account is locked
        if (user.LockoutEnd.HasValue && user.LockoutEnd > DateTime.UtcNow)
        {
            throw new UnauthorizedAccessException($"Account is locked. Please try again after {user.LockoutEnd.Value:g} UTC.");
        }

        // Verify password using BCrypt
        if (!_passwordHasher.VerifyPassword(request.Password, user.PasswordHash))
        {
            // Increment failed login attempts
            user.FailedLoginAttempts++;

            // Lock account after 5 failed attempts
            if (user.FailedLoginAttempts >= 5)
            {
                user.LockoutEnd = DateTime.UtcNow.AddMinutes(15);
            }

            await _context.SaveChangesAsync(cancellationToken);
            throw new UnauthorizedAccessException("Invalid email or password.");
        }

        // Check if account is active
        if (!user.IsActive)
        {
            throw new UnauthorizedAccessException("Your account has been deactivated. Please contact support.");
        }

        // Reset failed login attempts on successful login
        user.FailedLoginAttempts = 0;
        user.LockoutEnd = null;
        user.LastLoginAt = DateTime.UtcNow;

        // Generate JWT access token (1 hour)
        var accessToken = _jwtTokenService.GenerateAccessToken(user);
        var accessTokenExpiry = DateTime.UtcNow.AddMinutes(_jwtTokenService.AccessTokenExpirationMinutes);

        // Generate refresh token (7 days, or 30 days if remember me)
        var refreshTokenValue = _jwtTokenService.GenerateRefreshToken();
        var refreshTokenExpiry = request.RememberMe
            ? DateTime.UtcNow.AddDays(30)
            : DateTime.UtcNow.AddDays(_jwtTokenService.RefreshTokenExpirationDays);

        // Store refresh token in database
        var refreshToken = new RefreshTokenEntity
        {
            Id = Guid.NewGuid(),
            Token = refreshTokenValue,
            UserId = user.Id,
            ExpiresAt = refreshTokenExpiry,
            CreatedAt = DateTime.UtcNow,
            CreatedByIp = request.IpAddress
        };

        _context.RefreshTokens.Add(refreshToken);
        await _context.SaveChangesAsync(cancellationToken);

        // Return tokens and UserDto
        return new LoginResponseDto
        {
            User = MapToUserDto(user),
            AccessToken = accessToken,
            RefreshToken = refreshTokenValue,
            AccessTokenExpiresAt = accessTokenExpiry,
            RefreshTokenExpiresAt = refreshTokenExpiry,
            TokenType = "Bearer"
        };
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
