using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Admin.Users.Commands.UpdateUser;

/// <summary>
/// Handler for UpdateUserCommand.
/// </summary>
public class UpdateUserCommandHandler : IRequestHandler<UpdateUserCommand, bool>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<UpdateUserCommandHandler> _logger;

    public UpdateUserCommandHandler(
        IApplicationDbContext context,
        ILogger<UpdateUserCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<bool> Handle(UpdateUserCommand request, CancellationToken cancellationToken)
    {
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == request.Id, cancellationToken);

        if (user == null)
        {
            _logger.LogWarning("Attempted to update non-existent user with ID {UserId}", request.Id);
            return false;
        }

        // Update user properties
        user.FirstName = request.FirstName.Trim();
        user.LastName = request.LastName.Trim();
        user.Email = request.Email.ToLower().Trim();
        user.Role = request.Role;
        user.PhoneNumber = request.Phone?.Trim();
        user.CompanyName = request.CompanyName?.Trim();
        user.Department = request.Department?.Trim();
        user.JobTitle = request.JobTitle?.Trim();

        if (!string.IsNullOrEmpty(request.PreferredLanguage))
        {
            user.PreferredLanguage = request.PreferredLanguage;
        }

        if (!string.IsNullOrEmpty(request.TimeZone))
        {
            user.TimeZone = request.TimeZone;
        }

        user.LastModifiedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Updated user with ID {UserId}", user.Id);

        return true;
    }
}
