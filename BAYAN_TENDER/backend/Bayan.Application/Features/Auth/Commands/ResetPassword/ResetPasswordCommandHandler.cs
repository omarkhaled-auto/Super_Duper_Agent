using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Auth.Commands.ResetPassword;

/// <summary>
/// Handler for ResetPasswordCommand.
/// </summary>
public class ResetPasswordCommandHandler : IRequestHandler<ResetPasswordCommand, Unit>
{
    private readonly IApplicationDbContext _context;
    private readonly IPasswordHasher _passwordHasher;

    public ResetPasswordCommandHandler(
        IApplicationDbContext context,
        IPasswordHasher passwordHasher)
    {
        _context = context;
        _passwordHasher = passwordHasher;
    }

    public async Task<Unit> Handle(ResetPasswordCommand request, CancellationToken cancellationToken)
    {
        // Find user by email
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Email.ToLower() == request.Email.ToLower(), cancellationToken);

        if (user == null)
        {
            throw new UnauthorizedAccessException("Invalid reset token.");
        }

        // Validate reset token
        if (string.IsNullOrEmpty(user.PasswordResetToken) ||
            user.PasswordResetToken != request.Token)
        {
            throw new UnauthorizedAccessException("Invalid reset token.");
        }

        // Check token expiry
        if (!user.PasswordResetTokenExpiry.HasValue ||
            user.PasswordResetTokenExpiry < DateTime.UtcNow)
        {
            throw new UnauthorizedAccessException("Reset token has expired. Please request a new password reset.");
        }

        // Hash new password with BCrypt
        user.PasswordHash = _passwordHasher.HashPassword(request.NewPassword);

        // Clear reset token
        user.PasswordResetToken = null;
        user.PasswordResetTokenExpiry = null;

        // Reset lockout on successful password reset
        user.FailedLoginAttempts = 0;
        user.LockoutEnd = null;

        // Update last modified
        user.LastModifiedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return Unit.Value;
    }
}
