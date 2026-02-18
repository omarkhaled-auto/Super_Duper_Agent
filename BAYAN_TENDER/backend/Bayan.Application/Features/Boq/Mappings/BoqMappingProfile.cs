using AutoMapper;
using Bayan.Application.Features.Boq.Commands.AddBoqItem;
using Bayan.Application.Features.Boq.Commands.AddBoqSection;
using Bayan.Application.Features.Boq.Commands.UpdateBoqItem;
using Bayan.Application.Features.Boq.Commands.UpdateBoqSection;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Boq.Mappings;

/// <summary>
/// AutoMapper profile for BOQ entity mappings.
/// </summary>
public class BoqMappingProfile : Profile
{
    public BoqMappingProfile()
    {
        // BoqSection mappings
        CreateMap<BoqSection, BoqSectionDto>()
            .ForMember(dest => dest.Items, opt => opt.MapFrom(src => src.Items));

        CreateMap<BoqSection, BoqTreeNodeDto>()
            .ForMember(dest => dest.Children, opt => opt.Ignore())
            .ForMember(dest => dest.Items, opt => opt.MapFrom(src => src.Items));

        CreateMap<CreateBoqSectionDto, AddBoqSectionCommand>();
        CreateMap<UpdateBoqSectionDto, UpdateBoqSectionCommand>();

        CreateMap<AddBoqSectionCommand, BoqSection>()
            .ForMember(dest => dest.Id, opt => opt.Ignore())
            .ForMember(dest => dest.CreatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.UpdatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.Tender, opt => opt.Ignore())
            .ForMember(dest => dest.ParentSection, opt => opt.Ignore())
            .ForMember(dest => dest.ChildSections, opt => opt.Ignore())
            .ForMember(dest => dest.Items, opt => opt.Ignore());

        // BoqItem mappings
        CreateMap<BoqItem, BoqItemDto>();

        CreateMap<CreateBoqItemDto, AddBoqItemCommand>();
        CreateMap<UpdateBoqItemDto, UpdateBoqItemCommand>();

        CreateMap<AddBoqItemCommand, BoqItem>()
            .ForMember(dest => dest.Id, opt => opt.Ignore())
            .ForMember(dest => dest.CreatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.UpdatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.Tender, opt => opt.Ignore())
            .ForMember(dest => dest.Section, opt => opt.Ignore())
            .ForMember(dest => dest.BidPricings, opt => opt.Ignore())
            .ForMember(dest => dest.VendorItemRates, opt => opt.Ignore())
            .ForMember(dest => dest.ParentItem, opt => opt.Ignore())
            .ForMember(dest => dest.ChildItems, opt => opt.Ignore());

        // UnitOfMeasure mappings
        CreateMap<UnitOfMeasure, UomDto>();
    }
}
