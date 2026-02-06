using AutoMapper;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Clarifications.Mappings;

/// <summary>
/// AutoMapper profile for Clarification entity mappings.
/// </summary>
public class ClarificationMappingProfile : Profile
{
    public ClarificationMappingProfile()
    {
        // Basic Clarification to ClarificationDto mapping
        CreateMap<Clarification, ClarificationDto>()
            .ForMember(dest => dest.BidderName, opt => opt.MapFrom(src =>
                src.SubmittedByBidder != null ? src.SubmittedByBidder.CompanyName : null))
            .ForMember(dest => dest.SubmittedByUserName, opt => opt.MapFrom(src =>
                src.SubmittedByUser != null
                    ? $"{src.SubmittedByUser.FirstName} {src.SubmittedByUser.LastName}"
                    : null))
            .ForMember(dest => dest.AnsweredByName, opt => opt.MapFrom(src =>
                src.Answerer != null
                    ? $"{src.Answerer.FirstName} {src.Answerer.LastName}"
                    : null));

        // Detailed Clarification mapping
        CreateMap<Clarification, ClarificationDetailDto>()
            .ForMember(dest => dest.TenderTitle, opt => opt.MapFrom(src => src.Tender.Title))
            .ForMember(dest => dest.TenderReference, opt => opt.MapFrom(src => src.Tender.Reference))
            .ForMember(dest => dest.BidderName, opt => opt.MapFrom(src =>
                src.SubmittedByBidder != null ? src.SubmittedByBidder.CompanyName : null))
            .ForMember(dest => dest.BidderContactPerson, opt => opt.MapFrom(src =>
                src.SubmittedByBidder != null ? src.SubmittedByBidder.ContactPerson : null))
            .ForMember(dest => dest.BidderEmail, opt => opt.MapFrom(src =>
                src.SubmittedByBidder != null ? src.SubmittedByBidder.Email : null))
            .ForMember(dest => dest.SubmittedByUserName, opt => opt.MapFrom(src =>
                src.SubmittedByUser != null
                    ? $"{src.SubmittedByUser.FirstName} {src.SubmittedByUser.LastName}"
                    : null))
            .ForMember(dest => dest.AnsweredByName, opt => opt.MapFrom(src =>
                src.Answerer != null
                    ? $"{src.Answerer.FirstName} {src.Answerer.LastName}"
                    : null))
            .ForMember(dest => dest.RelatedDocumentName, opt => opt.MapFrom(src =>
                src.RelatedDocument != null ? src.RelatedDocument.FileName : null))
            .ForMember(dest => dest.DuplicateOfReference, opt => opt.MapFrom(src =>
                src.DuplicateOf != null ? src.DuplicateOf.ReferenceNumber : null))
            .ForMember(dest => dest.PublishedInBulletinNumber, opt => opt.MapFrom(src =>
                src.PublishedInBulletin != null ? src.PublishedInBulletin.BulletinNumber : (int?)null))
            // These will be populated manually in the handler
            .ForMember(dest => dest.AssignedToId, opt => opt.Ignore())
            .ForMember(dest => dest.AssignedToName, opt => opt.Ignore())
            .ForMember(dest => dest.RejectionReason, opt => opt.Ignore())
            .ForMember(dest => dest.Attachments, opt => opt.Ignore())
            .ForMember(dest => dest.History, opt => opt.Ignore());

        // ClarificationBulletin mapping
        CreateMap<ClarificationBulletin, ClarificationBulletinDto>()
            .ForMember(dest => dest.PublishedByName, opt => opt.MapFrom(src =>
                $"{src.Publisher.FirstName} {src.Publisher.LastName}"))
            .ForMember(dest => dest.QuestionCount, opt => opt.MapFrom(src =>
                src.Clarifications.Count))
            .ForMember(dest => dest.Questions, opt => opt.MapFrom(src =>
                src.Clarifications.OrderBy(c => c.ReferenceNumber)));

        // Clarification to ClarificationBulletinQuestionDto mapping
        CreateMap<Clarification, ClarificationBulletinQuestionDto>()
            .ForMember(dest => dest.Answer, opt => opt.MapFrom(src =>
                src.Answer ?? string.Empty));
    }
}
