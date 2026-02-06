using MediatR;

namespace Bayan.Application.Features.Admin.Users.Commands.ToggleUserActive;

/// <summary>
/// Command to toggle a user's active status.
/// </summary>
public record ToggleUserActiveCommand(Guid Id) : IRequest<ToggleUserActiveResult>;

/// <summary>
/// Result of ToggleUserActiveCommand execution.
/// </summary>
public record ToggleUserActiveResult
{
    /// <summary>
    /// Indicates whether the operation was successful.
    /// </summary>
    public bool Success { get; init; }

    /// <summary>
    /// The new active status of the user.
    /// </summary>
    public bool IsActive { get; init; }

    /// <summary>
    /// Error message if the operation failed.
    /// </summary>
    public string? ErrorMessage { get; init; }
}
