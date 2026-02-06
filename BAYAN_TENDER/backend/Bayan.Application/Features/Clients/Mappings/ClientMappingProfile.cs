using AutoMapper;
using Bayan.Application.Features.Clients.Commands.CreateClient;
using Bayan.Application.Features.Clients.Commands.UpdateClient;
using Bayan.Application.Features.Clients.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Clients.Mappings;

/// <summary>
/// AutoMapper profile for Client entity mappings.
/// </summary>
public class ClientMappingProfile : Profile
{
    public ClientMappingProfile()
    {
        // Entity to DTO
        CreateMap<Client, ClientDto>();

        // CreateClientDto to Command
        CreateMap<CreateClientDto, CreateClientCommand>();

        // UpdateClientDto to Command
        CreateMap<UpdateClientDto, UpdateClientCommand>();

        // Command to Entity (for direct mapping if needed)
        CreateMap<CreateClientCommand, Client>()
            .ForMember(dest => dest.Id, opt => opt.Ignore())
            .ForMember(dest => dest.IsActive, opt => opt.MapFrom(_ => true))
            .ForMember(dest => dest.CreatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.UpdatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.CreatedBy, opt => opt.Ignore())
            .ForMember(dest => dest.LastModifiedBy, opt => opt.Ignore())
            .ForMember(dest => dest.LastModifiedAt, opt => opt.Ignore());
    }
}
