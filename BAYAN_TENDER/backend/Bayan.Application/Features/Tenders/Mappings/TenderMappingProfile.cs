using AutoMapper;
using Bayan.Application.Features.Tenders.Commands.CreateTender;
using Bayan.Application.Features.Tenders.Commands.UpdateTender;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Tenders.Mappings;

/// <summary>
/// AutoMapper profile for Tender entity mappings.
/// </summary>
public class TenderMappingProfile : Profile
{
    public TenderMappingProfile()
    {
        // Entity to DTOs
        CreateMap<Tender, TenderDto>()
            .ForMember(dest => dest.ClientName, opt => opt.MapFrom(src => src.Client.Name))
            .ForMember(dest => dest.BidderCount, opt => opt.MapFrom(src => src.TenderBidders.Count))
            .ForMember(dest => dest.BidCount, opt => opt.MapFrom(src => src.BidSubmissions.Count));

        CreateMap<Tender, TenderListDto>()
            .ForMember(dest => dest.ClientName, opt => opt.MapFrom(src => src.Client.Name))
            .ForMember(dest => dest.BidderCount, opt => opt.MapFrom(src => src.TenderBidders.Count))
            .ForMember(dest => dest.DaysRemaining, opt => opt.MapFrom(src =>
                (int)(src.SubmissionDeadline - DateTime.UtcNow).TotalDays));

        CreateMap<Tender, TenderDetailDto>()
            .ForMember(dest => dest.ClientName, opt => opt.MapFrom(src => src.Client.Name))
            .ForMember(dest => dest.CreatedByName, opt => opt.MapFrom(src => src.Creator != null ? src.Creator.FullName : null))
            .ForMember(dest => dest.EvaluationCriteria, opt => opt.MapFrom(src => src.EvaluationCriteria))
            .ForMember(dest => dest.Bidders, opt => opt.MapFrom(src => src.TenderBidders))
            .ForMember(dest => dest.BidCount, opt => opt.MapFrom(src => src.BidSubmissions.Count))
            .ForMember(dest => dest.DocumentCount, opt => opt.MapFrom(src => src.Documents.Count))
            .ForMember(dest => dest.ClarificationCount, opt => opt.MapFrom(src => src.Clarifications.Count));

        // EvaluationCriteria mappings
        CreateMap<EvaluationCriteria, EvaluationCriterionDto>();

        CreateMap<CreateEvaluationCriterionDto, EvaluationCriteria>()
            .ForMember(dest => dest.Id, opt => opt.Ignore())
            .ForMember(dest => dest.TenderId, opt => opt.Ignore())
            .ForMember(dest => dest.Tender, opt => opt.Ignore())
            .ForMember(dest => dest.TechnicalScores, opt => opt.Ignore())
            .ForMember(dest => dest.CreatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.UpdatedAt, opt => opt.Ignore());

        // TenderBidder mappings
        CreateMap<TenderBidder, TenderBidderDto>()
            .ForMember(dest => dest.CompanyName, opt => opt.MapFrom(src => src.Bidder.CompanyName))
            .ForMember(dest => dest.ContactPerson, opt => opt.MapFrom(src => src.Bidder.ContactPerson))
            .ForMember(dest => dest.Email, opt => opt.MapFrom(src => src.Bidder.Email));

        // CreateTenderDto to Command
        CreateMap<CreateTenderDto, CreateTenderCommand>();

        // UpdateTenderDto to Command
        CreateMap<UpdateTenderDto, UpdateTenderCommand>()
            .ForMember(dest => dest.Id, opt => opt.Ignore());

        // Command to Entity (for direct mapping if needed)
        CreateMap<CreateTenderCommand, Tender>()
            .ForMember(dest => dest.Id, opt => opt.Ignore())
            .ForMember(dest => dest.Reference, opt => opt.Ignore())
            .ForMember(dest => dest.Status, opt => opt.Ignore())
            .ForMember(dest => dest.PublishedAt, opt => opt.Ignore())
            .ForMember(dest => dest.AwardedAt, opt => opt.Ignore())
            .ForMember(dest => dest.CreatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.UpdatedAt, opt => opt.Ignore())
            .ForMember(dest => dest.CreatedBy, opt => opt.Ignore())
            .ForMember(dest => dest.LastModifiedBy, opt => opt.Ignore())
            .ForMember(dest => dest.LastModifiedAt, opt => opt.Ignore())
            .ForMember(dest => dest.Client, opt => opt.Ignore())
            .ForMember(dest => dest.Creator, opt => opt.Ignore())
            .ForMember(dest => dest.EvaluationCriteria, opt => opt.Ignore())
            .ForMember(dest => dest.TenderBidders, opt => opt.Ignore())
            .ForMember(dest => dest.Documents, opt => opt.Ignore())
            .ForMember(dest => dest.Addenda, opt => opt.Ignore())
            .ForMember(dest => dest.Clarifications, opt => opt.Ignore())
            .ForMember(dest => dest.ClarificationBulletins, opt => opt.Ignore())
            .ForMember(dest => dest.BoqSections, opt => opt.Ignore())
            .ForMember(dest => dest.BoqItems, opt => opt.Ignore())
            .ForMember(dest => dest.BidSubmissions, opt => opt.Ignore())
            .ForMember(dest => dest.EvaluationPanels, opt => opt.Ignore())
            .ForMember(dest => dest.TechnicalScores, opt => opt.Ignore())
            .ForMember(dest => dest.EvaluationState, opt => opt.Ignore())
            .ForMember(dest => dest.CommercialScores, opt => opt.Ignore())
            .ForMember(dest => dest.CombinedScorecards, opt => opt.Ignore())
            .ForMember(dest => dest.BidExceptions, opt => opt.Ignore())
            .ForMember(dest => dest.ApprovalWorkflow, opt => opt.Ignore())
            .ForMember(dest => dest.VendorPricingSnapshots, opt => opt.Ignore())
            .ForMember(dest => dest.EmailLogs, opt => opt.Ignore());
    }
}
