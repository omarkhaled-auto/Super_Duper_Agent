using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Admin.Users.Commands.ToggleUserActive;

/// <summary>
/// Handler for ToggleUserActiveCommand.
/// </summary>
public class ToggleUserActiveCommandHandler : IRequestHandler<ToggleUserActiveCommand, ToggleUserActiveResult>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<ToggleUserActiveCommandHandler> _logger;

    public ToggleUserActiveCommandHandler(
        IApplicationDbContext context,
        ILogger<ToggleUserActiveCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<ToggleUserActiveResult> Handle(ToggleUserActiveCommand request, CancellationToken cancellationToken)
    {
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == request.Id, cancellationToken);

        if (user == null)
        {
            _logger.LogWarning("Attempted to toggle active status for non-existent user with ID {UserId}", request.Id);
            return new ToggleUserActiveResult
            {
                Success = false,
                ErrorMessage = "User not found."
            };
        }

        // Toggle the active status
        user.IsActive = !user.IsActive;
        user.LastModifiedAt = DateTime.UtcNow;

        // If deactivating, clear any existing refresh tokens
        if (!user.IsActive)
        {
            user.RefreshToken = null;
            user.RefreshTokenExpiry = null;
        }

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Toggled active status for user {UserId} to {IsActive}",
            user.Id,
            user.IsActive);

        return new ToggleUserActiveResult
        {
            Success = true,
            IsActive = user.IsActive
        };
    }
}
