using AutoMapper;
using Bayan.Application.Features.Bidders.Commands.CreateBidder;
using Bayan.Application.Features.Bidders.Commands.UpdateBidder;
using Bayan.Application.Features.Bidders.DTOs;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Bidders.Mappings;

/// <summary>
/// AutoMapper profile for Bidder entity mappings.
/// </summary>
public class BidderMappingProfile : Profile
{
    public BidderMappingProfile()
    {
        // Entity to DTOs
        CreateMap<Bidder, BidderDto>();

        CreateMap<Bidder, BidderDetailDto>()
            .ForMember(dest => dest.TenderCount, opt => opt.Ignore());

        // DTOs to Commands
        CreateMap<CreateBidderDto, CreateBidderCommand>();
        CreateMap<UpdateBidderDto, UpdateBidderCommand>();

        // Command to Entity (for direct mapping if needed)
        CreateMap<CreateBidderCommand, Bidder>()
            .ForMember(dest => dest.Id, opt => opt.Ignore())
            .ForMember(dest => dest.PrequalificationStatus, opt => opt.Ignore())
            .ForMember(dest => dest.IsActive, opt => opt.MapFrom(_ => true))
            .ForMember(dest => dest.CompanyProfilePath, opt => opt.Ignore())
            .ForMember(dest => dest.PasswordHash, opt => opt.Ignore())
            .ForMember(dest => dest.LastLoginAt, opt => opt.Ignore())
            .ForMember(dest => dest.CreatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.UpdatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.TenderBidders, opt => opt.Ignore())
            .ForMember(dest => dest.Clarifications, opt => opt.Ignore())
            .ForMember(dest => dest.AddendumAcknowledgments, opt => opt.Ignore())
            .ForMember(dest => dest.BidSubmissions, opt => opt.Ignore())
            .ForMember(dest => dest.TechnicalScores, opt => opt.Ignore())
            .ForMember(dest => dest.CommercialScores, opt => opt.Ignore())
            .ForMember(dest => dest.CombinedScorecards, opt => opt.Ignore())
            .ForMember(dest => dest.BidExceptions, opt => opt.Ignore())
            .ForMember(dest => dest.VendorPricingSnapshots, opt => opt.Ignore());

        // TenderBidder to TenderBidderDto
        CreateMap<TenderBidder, TenderBidderDto>()
            .ForMember(dest => dest.CompanyName, opt => opt.MapFrom(src => src.Bidder.CompanyName))
            .ForMember(dest => dest.ContactPerson, opt => opt.MapFrom(src => src.Bidder.ContactPerson))
            .ForMember(dest => dest.Email, opt => opt.MapFrom(src => src.Bidder.Email));
    }
}
