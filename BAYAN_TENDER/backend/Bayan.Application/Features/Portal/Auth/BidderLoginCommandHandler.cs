using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Auth;

/// <summary>
/// Handler for BidderLoginCommand.
/// </summary>
public class BidderLoginCommandHandler : IRequestHandler<BidderLoginCommand, BidderLoginResponseDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtTokenService _jwtTokenService;

    public BidderLoginCommandHandler(
        IApplicationDbContext context,
        IPasswordHasher passwordHasher,
        IJwtTokenService jwtTokenService)
    {
        _context = context;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
    }

    public async Task<BidderLoginResponseDto> Handle(BidderLoginCommand request, CancellationToken cancellationToken)
    {
        // Find bidder by email
        var bidder = await _context.Bidders
            .Include(b => b.TenderBidders)
                .ThenInclude(tb => tb.Tender)
            .FirstOrDefaultAsync(b => b.Email.ToLower() == request.Email.ToLower(), cancellationToken);

        if (bidder == null)
        {
            throw new UnauthorizedAccessException("Invalid email or password.");
        }

        // Check if bidder is active
        if (!bidder.IsActive)
        {
            throw new UnauthorizedAccessException("Your account has been deactivated. Please contact the tender administrator.");
        }

        // Check if bidder has a password set
        if (string.IsNullOrEmpty(bidder.PasswordHash))
        {
            throw new UnauthorizedAccessException("Account not activated. Please set your password using the activation link sent to your email.");
        }

        // Verify password using BCrypt
        if (!_passwordHasher.VerifyPassword(request.Password, bidder.PasswordHash))
        {
            throw new UnauthorizedAccessException("Invalid email or password.");
        }

        // If tender ID is provided, validate access
        if (request.TenderId.HasValue)
        {
            var tenderBidder = bidder.TenderBidders
                .FirstOrDefault(tb => tb.TenderId == request.TenderId.Value);

            if (tenderBidder == null)
            {
                throw new UnauthorizedAccessException("You do not have access to this tender.");
            }

            if (tenderBidder.QualificationStatus != QualificationStatus.Qualified)
            {
                throw new UnauthorizedAccessException($"You are not qualified for this tender. Current status: {tenderBidder.QualificationStatus}");
            }
        }

        // Update last login timestamp
        bidder.LastLoginAt = DateTime.UtcNow;

        // Generate JWT access token
        var accessToken = _jwtTokenService.GenerateBidderAccessToken(bidder);
        var accessTokenExpiry = DateTime.UtcNow.AddMinutes(_jwtTokenService.AccessTokenExpirationMinutes);

        // Generate refresh token
        var refreshTokenValue = _jwtTokenService.GenerateRefreshToken();
        var refreshTokenExpiry = request.RememberMe
            ? DateTime.UtcNow.AddDays(30)
            : DateTime.UtcNow.AddDays(_jwtTokenService.RefreshTokenExpirationDays);

        // Store refresh token in database
        var refreshToken = new BidderRefreshToken
        {
            Id = Guid.NewGuid(),
            Token = refreshTokenValue,
            BidderId = bidder.Id,
            ExpiresAt = refreshTokenExpiry,
            CreatedAt = DateTime.UtcNow,
            CreatedByIp = request.IpAddress
        };

        _context.BidderRefreshTokens.Add(refreshToken);
        await _context.SaveChangesAsync(cancellationToken);

        // Build tender access list
        var tenderAccess = bidder.TenderBidders
            .Where(tb => tb.QualificationStatus == QualificationStatus.Qualified)
            .Select(tb => new BidderTenderAccessDto
            {
                TenderId = tb.TenderId,
                TenderTitle = tb.Tender.Title,
                TenderReference = tb.Tender.Reference,
                QualificationStatus = tb.QualificationStatus.ToString()
            })
            .ToList();

        return new BidderLoginResponseDto
        {
            Bidder = new BidderInfoDto
            {
                Id = bidder.Id,
                CompanyName = bidder.CompanyName,
                ContactPerson = bidder.ContactPerson,
                Email = bidder.Email,
                Phone = bidder.Phone,
                TradeSpecialization = bidder.TradeSpecialization,
                TenderAccess = tenderAccess
            },
            AccessToken = accessToken,
            RefreshToken = refreshTokenValue,
            AccessTokenExpiresAt = accessTokenExpiry,
            RefreshTokenExpiresAt = refreshTokenExpiry,
            TokenType = "Bearer"
        };
    }
}
