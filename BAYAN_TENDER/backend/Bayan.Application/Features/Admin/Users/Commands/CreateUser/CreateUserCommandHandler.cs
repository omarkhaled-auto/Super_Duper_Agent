using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Admin.Users.Commands.CreateUser;

/// <summary>
/// Handler for CreateUserCommand.
/// </summary>
public class CreateUserCommandHandler : IRequestHandler<CreateUserCommand, CreateUserResult>
{
    private readonly IApplicationDbContext _context;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IEmailService _emailService;
    private readonly ILogger<CreateUserCommandHandler> _logger;

    public CreateUserCommandHandler(
        IApplicationDbContext context,
        IPasswordHasher passwordHasher,
        IEmailService emailService,
        ILogger<CreateUserCommandHandler> logger)
    {
        _context = context;
        _passwordHasher = passwordHasher;
        _emailService = emailService;
        _logger = logger;
    }

    public async Task<CreateUserResult> Handle(CreateUserCommand request, CancellationToken cancellationToken)
    {
        // Use admin-provided password if set, otherwise generate temporary password
        var temporaryPassword = string.IsNullOrWhiteSpace(request.Password)
            ? _passwordHasher.GenerateTemporaryPassword()
            : null;
        var actualPassword = temporaryPassword ?? request.Password!;
        var passwordHash = _passwordHasher.HashPassword(actualPassword);

        // Create user entity
        var user = new User
        {
            Id = Guid.NewGuid(),
            FirstName = request.FirstName.Trim(),
            LastName = request.LastName.Trim(),
            Email = request.Email.ToLower().Trim(),
            PasswordHash = passwordHash,
            Role = request.Role,
            PhoneNumber = request.Phone?.Trim(),
            CompanyName = request.CompanyName?.Trim(),
            Department = request.Department?.Trim(),
            JobTitle = request.JobTitle?.Trim(),
            IsActive = true,
            EmailVerified = true,
            CreatedAt = DateTime.UtcNow
        };

        _context.Users.Add(user);
        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Created new user with ID {UserId} and email {Email}", user.Id, user.Email);

        // Optionally send invitation email (only if temp password was generated)
        var emailSent = false;
        if (request.SendInvitationEmail && temporaryPassword != null)
        {
            try
            {
                await _emailService.SendUserInvitationEmailAsync(
                    user.Email,
                    user.FirstName,
                    temporaryPassword,
                    cancellationToken);
                emailSent = true;
                _logger.LogInformation("Sent invitation email to user {UserId}", user.Id);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to send invitation email to user {UserId}", user.Id);
            }
        }

        return new CreateUserResult
        {
            UserId = user.Id,
            // Only return the temporary password if one was generated and email wasn't sent
            TemporaryPassword = emailSent ? null : temporaryPassword,
            InvitationEmailSent = emailSent
        };
    }
}
