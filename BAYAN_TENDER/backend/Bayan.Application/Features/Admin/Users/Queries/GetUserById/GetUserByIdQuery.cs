using MediatR;

namespace Bayan.Application.Features.Admin.Users.Queries.GetUserById;

/// <summary>
/// Query to retrieve a user by their ID.
/// </summary>
public record GetUserByIdQuery(Guid Id) : IRequest<UserDto?>;
