using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Auth.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Auth.Commands.RefreshToken;

/// <summary>
/// Handler for RefreshTokenCommand.
/// </summary>
public class RefreshTokenCommandHandler : IRequestHandler<RefreshTokenCommand, TokenDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IJwtTokenService _jwtTokenService;

    public RefreshTokenCommandHandler(
        IApplicationDbContext context,
        IJwtTokenService jwtTokenService)
    {
        _context = context;
        _jwtTokenService = jwtTokenService;
    }

    public async Task<TokenDto> Handle(RefreshTokenCommand request, CancellationToken cancellationToken)
    {
        // Find the refresh token in the database
        var refreshToken = await _context.RefreshTokens
            .Include(rt => rt.User)
            .FirstOrDefaultAsync(rt => rt.Token == request.RefreshToken, cancellationToken);

        if (refreshToken == null)
        {
            throw new UnauthorizedAccessException("Invalid refresh token.");
        }

        // Check if token is active
        if (!refreshToken.IsActive)
        {
            throw new UnauthorizedAccessException("Refresh token has expired or been revoked.");
        }

        // Check if user is still active
        if (!refreshToken.User.IsActive)
        {
            throw new UnauthorizedAccessException("User account has been deactivated.");
        }

        var user = refreshToken.User;

        // Revoke the old refresh token (token rotation)
        refreshToken.IsRevoked = true;
        refreshToken.RevokedAt = DateTime.UtcNow;
        refreshToken.RevokedByIp = request.IpAddress;

        // Generate new access token
        var newAccessToken = _jwtTokenService.GenerateAccessToken(user);
        var accessTokenExpiry = DateTime.UtcNow.AddMinutes(_jwtTokenService.AccessTokenExpirationMinutes);

        // Generate new refresh token
        var newRefreshTokenValue = _jwtTokenService.GenerateRefreshToken();
        var refreshTokenExpiry = DateTime.UtcNow.AddDays(_jwtTokenService.RefreshTokenExpirationDays);

        // Mark old token as replaced
        refreshToken.ReplacedByToken = newRefreshTokenValue;

        // Store new refresh token in database
        var newRefreshToken = new Domain.Entities.RefreshToken
        {
            Id = Guid.NewGuid(),
            Token = newRefreshTokenValue,
            UserId = user.Id,
            ExpiresAt = refreshTokenExpiry,
            CreatedAt = DateTime.UtcNow,
            CreatedByIp = request.IpAddress
        };

        _context.RefreshTokens.Add(newRefreshToken);
        await _context.SaveChangesAsync(cancellationToken);

        return new TokenDto
        {
            AccessToken = newAccessToken,
            RefreshToken = newRefreshTokenValue,
            AccessTokenExpiresAt = accessTokenExpiry,
            RefreshTokenExpiresAt = refreshTokenExpiry,
            TokenType = "Bearer"
        };
    }
}
