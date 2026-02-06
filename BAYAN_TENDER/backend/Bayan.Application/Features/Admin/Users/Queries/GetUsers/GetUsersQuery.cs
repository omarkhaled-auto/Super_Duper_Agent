using Bayan.Application.Common.Models;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Admin.Users.Queries.GetUsers;

/// <summary>
/// Query to retrieve a paginated list of users with optional filtering.
/// </summary>
public record GetUsersQuery : IRequest<PaginatedList<UserDto>>
{
    /// <summary>
    /// Page number (1-based). Default is 1.
    /// </summary>
    public int Page { get; init; } = 1;

    /// <summary>
    /// Number of items per page. Default is 10.
    /// </summary>
    public int PageSize { get; init; } = 10;

    /// <summary>
    /// Search term to filter by name, email, or company.
    /// </summary>
    public string? Search { get; init; }

    /// <summary>
    /// Filter by user role.
    /// </summary>
    public UserRole? Role { get; init; }

    /// <summary>
    /// Filter by active status.
    /// </summary>
    public bool? IsActive { get; init; }
}
