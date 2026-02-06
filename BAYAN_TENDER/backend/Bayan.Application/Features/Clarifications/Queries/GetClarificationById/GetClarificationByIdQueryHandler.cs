using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Queries.GetClarificationById;

/// <summary>
/// Handler for the GetClarificationByIdQuery.
/// </summary>
public class GetClarificationByIdQueryHandler : IRequestHandler<GetClarificationByIdQuery, ClarificationDetailDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetClarificationByIdQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClarificationDetailDto?> Handle(
        GetClarificationByIdQuery request,
        CancellationToken cancellationToken)
    {
        var clarification = await _context.Clarifications
            .AsNoTracking()
            .Include(c => c.Tender)
            .Include(c => c.SubmittedByBidder)
            .Include(c => c.SubmittedByUser)
            .Include(c => c.Answerer)
            .Include(c => c.RelatedDocument)
            .Include(c => c.DuplicateOf)
            .Include(c => c.PublishedInBulletin)
            .Where(c => c.TenderId == request.TenderId && c.Id == request.ClarificationId)
            .FirstOrDefaultAsync(cancellationToken);

        if (clarification == null)
        {
            return null;
        }

        var dto = _mapper.Map<ClarificationDetailDto>(clarification);

        // Map tender info
        dto.TenderTitle = clarification.Tender.Title;
        dto.TenderReference = clarification.Tender.Reference;

        // Map bidder info
        if (clarification.SubmittedByBidder != null)
        {
            dto.BidderName = clarification.SubmittedByBidder.CompanyName;
            dto.BidderContactPerson = clarification.SubmittedByBidder.ContactPerson;
            dto.BidderEmail = clarification.SubmittedByBidder.Email;
        }

        // Map user info
        if (clarification.SubmittedByUser != null)
        {
            dto.SubmittedByUserName = $"{clarification.SubmittedByUser.FirstName} {clarification.SubmittedByUser.LastName}";
        }

        // Map answerer info
        if (clarification.Answerer != null)
        {
            dto.AnsweredByName = $"{clarification.Answerer.FirstName} {clarification.Answerer.LastName}";
        }

        // Map related document info
        if (clarification.RelatedDocument != null)
        {
            dto.RelatedDocumentName = clarification.RelatedDocument.FileName;
        }

        // Map duplicate reference
        if (clarification.DuplicateOf != null)
        {
            dto.DuplicateOfReference = clarification.DuplicateOf.ReferenceNumber;
        }

        // Map bulletin info
        if (clarification.PublishedInBulletin != null)
        {
            dto.PublishedInBulletinNumber = clarification.PublishedInBulletin.BulletinNumber;
        }

        // Note: Attachments and History would be populated from related tables
        // if those tables exist in the domain model

        return dto;
    }
}
