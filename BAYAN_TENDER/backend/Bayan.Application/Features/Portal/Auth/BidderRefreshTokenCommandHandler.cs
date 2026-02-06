using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Auth.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Auth;

/// <summary>
/// Handler for BidderRefreshTokenCommand.
/// </summary>
public class BidderRefreshTokenCommandHandler : IRequestHandler<BidderRefreshTokenCommand, TokenDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IJwtTokenService _jwtTokenService;

    public BidderRefreshTokenCommandHandler(
        IApplicationDbContext context,
        IJwtTokenService jwtTokenService)
    {
        _context = context;
        _jwtTokenService = jwtTokenService;
    }

    public async Task<TokenDto> Handle(BidderRefreshTokenCommand request, CancellationToken cancellationToken)
    {
        // Find the refresh token
        var refreshToken = await _context.BidderRefreshTokens
            .Include(rt => rt.Bidder)
            .FirstOrDefaultAsync(rt => rt.Token == request.RefreshToken, cancellationToken);

        if (refreshToken == null)
        {
            throw new UnauthorizedAccessException("Invalid refresh token.");
        }

        // Validate the token
        if (refreshToken.IsRevoked)
        {
            // If someone tries to use a revoked token, revoke all tokens for this bidder
            // This handles the case of a compromised token chain
            await RevokeAllBidderTokensAsync(refreshToken.BidderId, request.IpAddress, cancellationToken);
            throw new UnauthorizedAccessException("Token has been revoked. All tokens have been invalidated for security.");
        }

        if (refreshToken.IsExpired)
        {
            throw new UnauthorizedAccessException("Refresh token has expired. Please login again.");
        }

        var bidder = refreshToken.Bidder;

        if (!bidder.IsActive)
        {
            throw new UnauthorizedAccessException("Your account has been deactivated.");
        }

        // Revoke the old refresh token
        refreshToken.IsRevoked = true;
        refreshToken.RevokedAt = DateTime.UtcNow;
        refreshToken.RevokedByIp = request.IpAddress;

        // Generate new tokens
        var newAccessToken = _jwtTokenService.GenerateBidderAccessToken(bidder);
        var newAccessTokenExpiry = DateTime.UtcNow.AddMinutes(_jwtTokenService.AccessTokenExpirationMinutes);

        var newRefreshTokenValue = _jwtTokenService.GenerateRefreshToken();
        var newRefreshTokenExpiry = DateTime.UtcNow.AddDays(_jwtTokenService.RefreshTokenExpirationDays);

        // Update old token with replacement info
        refreshToken.ReplacedByToken = newRefreshTokenValue;

        // Store new refresh token
        var newRefreshToken = new BidderRefreshToken
        {
            Id = Guid.NewGuid(),
            Token = newRefreshTokenValue,
            BidderId = bidder.Id,
            ExpiresAt = newRefreshTokenExpiry,
            CreatedAt = DateTime.UtcNow,
            CreatedByIp = request.IpAddress
        };

        _context.BidderRefreshTokens.Add(newRefreshToken);
        await _context.SaveChangesAsync(cancellationToken);

        return new TokenDto
        {
            AccessToken = newAccessToken,
            RefreshToken = newRefreshTokenValue,
            AccessTokenExpiresAt = newAccessTokenExpiry,
            RefreshTokenExpiresAt = newRefreshTokenExpiry,
            TokenType = "Bearer"
        };
    }

    private async Task RevokeAllBidderTokensAsync(Guid bidderId, string? ipAddress, CancellationToken cancellationToken)
    {
        var activeTokens = await _context.BidderRefreshTokens
            .Where(rt => rt.BidderId == bidderId && !rt.IsRevoked)
            .ToListAsync(cancellationToken);

        foreach (var token in activeTokens)
        {
            token.IsRevoked = true;
            token.RevokedAt = DateTime.UtcNow;
            token.RevokedByIp = ipAddress;
        }

        await _context.SaveChangesAsync(cancellationToken);
    }
}
