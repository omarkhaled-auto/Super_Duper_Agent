using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Auth;

/// <summary>
/// Handler for ActivateBidderAccountCommand.
/// </summary>
public class ActivateBidderAccountCommandHandler : IRequestHandler<ActivateBidderAccountCommand, Unit>
{
    private readonly IApplicationDbContext _context;
    private readonly IPasswordHasher _passwordHasher;

    public ActivateBidderAccountCommandHandler(
        IApplicationDbContext context,
        IPasswordHasher passwordHasher)
    {
        _context = context;
        _passwordHasher = passwordHasher;
    }

    public async Task<Unit> Handle(ActivateBidderAccountCommand request, CancellationToken cancellationToken)
    {
        // Find bidder by email (case-insensitive)
        var bidder = await _context.Bidders
            .FirstOrDefaultAsync(b => b.Email.ToLower() == request.Email.ToLower(), cancellationToken);

        if (bidder == null)
        {
            throw new UnauthorizedAccessException("Invalid activation token.");
        }

        // Validate activation token
        if (string.IsNullOrEmpty(bidder.ActivationToken) ||
            bidder.ActivationToken != request.ActivationToken)
        {
            throw new UnauthorizedAccessException("Invalid activation token.");
        }

        // Check token expiry
        if (!bidder.ActivationTokenExpiry.HasValue ||
            bidder.ActivationTokenExpiry < DateTime.UtcNow)
        {
            throw new UnauthorizedAccessException("Activation token has expired. Please contact the tender administrator for a new invitation.");
        }

        // Validate passwords match
        if (request.Password != request.ConfirmPassword)
        {
            throw new InvalidOperationException("Passwords do not match.");
        }

        // Hash new password with BCrypt
        bidder.PasswordHash = _passwordHasher.HashPassword(request.Password);

        // Clear activation token
        bidder.ActivationToken = null;
        bidder.ActivationTokenExpiry = null;

        // Update timestamp
        bidder.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return Unit.Value;
    }
}
