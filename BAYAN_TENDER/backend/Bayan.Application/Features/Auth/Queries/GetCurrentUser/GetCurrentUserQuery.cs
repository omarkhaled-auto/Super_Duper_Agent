using Bayan.Application.Features.Auth.DTOs;
using MediatR;

namespace Bayan.Application.Features.Auth.Queries.GetCurrentUser;

/// <summary>
/// Query for getting the current authenticated user.
/// </summary>
public class GetCurrentUserQuery : IRequest<UserDto>
{
    // The user ID is injected from the current user context in the handler
}
