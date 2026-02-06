using AutoMapper;
using Bayan.Application.Features.Approval.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Approval.Mappings;

/// <summary>
/// AutoMapper profile for Approval entity mappings.
/// </summary>
public class ApprovalMappingProfile : Profile
{
    public ApprovalMappingProfile()
    {
        // Entity to DTO mappings
        CreateMap<ApprovalWorkflow, ApprovalWorkflowDto>()
            .ForMember(dest => dest.TenderReference, opt => opt.MapFrom(src => src.Tender.Reference))
            .ForMember(dest => dest.TenderTitle, opt => opt.MapFrom(src => src.Tender.Title))
            .ForMember(dest => dest.InitiatedByName, opt => opt.MapFrom(src => src.Initiator.FullName))
            .ForMember(dest => dest.CurrentLevel, opt => opt.Ignore())
            .ForMember(dest => dest.TotalLevels, opt => opt.MapFrom(src => src.Levels.Count));

        CreateMap<ApprovalLevel, ApprovalLevelDto>()
            .ForMember(dest => dest.ApproverName, opt => opt.MapFrom(src => src.Approver.FullName))
            .ForMember(dest => dest.ApproverEmail, opt => opt.MapFrom(src => src.Approver.Email));

        CreateMap<ApprovalLevel, ApprovalHistoryDto>()
            .ForMember(dest => dest.ApproverName, opt => opt.MapFrom(src => src.Approver.FullName))
            .ForMember(dest => dest.ApproverEmail, opt => opt.MapFrom(src => src.Approver.Email))
            .ForMember(dest => dest.ApproverJobTitle, opt => opt.MapFrom(src => src.Approver.JobTitle));
    }
}
