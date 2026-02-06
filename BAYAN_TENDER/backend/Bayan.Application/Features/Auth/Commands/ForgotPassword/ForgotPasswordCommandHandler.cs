using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;
using System.Security.Cryptography;

namespace Bayan.Application.Features.Auth.Commands.ForgotPassword;

/// <summary>
/// Handler for ForgotPasswordCommand.
/// </summary>
public class ForgotPasswordCommandHandler : IRequestHandler<ForgotPasswordCommand, Unit>
{
    private readonly IApplicationDbContext _context;
    private readonly IEmailService _emailService;

    public ForgotPasswordCommandHandler(
        IApplicationDbContext context,
        IEmailService emailService)
    {
        _context = context;
        _emailService = emailService;
    }

    public async Task<Unit> Handle(ForgotPasswordCommand request, CancellationToken cancellationToken)
    {
        // Find user by email (case-insensitive)
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Email.ToLower() == request.Email.ToLower(), cancellationToken);

        // Always return success to prevent email enumeration attacks
        // But only send email if user exists
        if (user != null && user.IsActive)
        {
            // Generate secure reset token
            var resetToken = GenerateSecureToken();

            // Store token with 1-hour expiry
            user.PasswordResetToken = resetToken;
            user.PasswordResetTokenExpiry = DateTime.UtcNow.AddHours(1);

            await _context.SaveChangesAsync(cancellationToken);

            // Send password reset email
            await _emailService.SendPasswordResetEmailAsync(
                user.Email,
                user.FirstName,
                resetToken,
                request.ResetUrl,
                cancellationToken);
        }

        // Always return success to prevent email enumeration
        return Unit.Value;
    }

    private static string GenerateSecureToken()
    {
        var randomBytes = new byte[64];
        using var rng = RandomNumberGenerator.Create();
        rng.GetBytes(randomBytes);
        return Convert.ToBase64String(randomBytes)
            .Replace("+", "-")
            .Replace("/", "_")
            .Replace("=", "");
    }
}
