using AutoMapper;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Admin.Users;

/// <summary>
/// AutoMapper profile for User entity mappings.
/// </summary>
public class UserMappingProfile : Profile
{
    public UserMappingProfile()
    {
        CreateMap<User, UserDto>()
            .ForMember(dest => dest.UpdatedAt, opt => opt.MapFrom(src => src.LastModifiedAt));
    }
}
