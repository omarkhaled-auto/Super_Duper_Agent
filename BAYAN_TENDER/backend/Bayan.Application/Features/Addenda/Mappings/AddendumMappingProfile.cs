using AutoMapper;
using Bayan.Application.Features.Addenda.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Addenda.Mappings;

/// <summary>
/// AutoMapper profile for Addendum mappings.
/// </summary>
public class AddendumMappingProfile : Profile
{
    public AddendumMappingProfile()
    {
        CreateMap<Addendum, AddendumDto>();

        CreateMap<Addendum, AddendumDetailDto>()
            .ForMember(dest => dest.TenderTitle, opt => opt.MapFrom(src => src.Tender.Title))
            .ForMember(dest => dest.TenderReference, opt => opt.MapFrom(src => src.Tender.Reference))
            .ForMember(dest => dest.IssuedByName, opt => opt.MapFrom(src =>
                src.Issuer != null ? $"{src.Issuer.FirstName} {src.Issuer.LastName}" : null))
            .ForMember(dest => dest.TotalBidders, opt => opt.Ignore())
            .ForMember(dest => dest.AcknowledgedCount, opt => opt.Ignore());

        CreateMap<AddendumAcknowledgment, AddendumAcknowledgmentDto>()
            .ForMember(dest => dest.BidderName, opt => opt.MapFrom(src => src.Bidder.CompanyName))
            .ForMember(dest => dest.BidderContactPerson, opt => opt.MapFrom(src => src.Bidder.ContactPerson))
            .ForMember(dest => dest.BidderEmail, opt => opt.MapFrom(src => src.Bidder.Email));
    }
}
