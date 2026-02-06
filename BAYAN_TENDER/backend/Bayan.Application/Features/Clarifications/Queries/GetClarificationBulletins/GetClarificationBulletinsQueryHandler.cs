using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Queries.GetClarificationBulletins;

/// <summary>
/// Handler for the GetClarificationBulletinsQuery.
/// </summary>
public class GetClarificationBulletinsQueryHandler : IRequestHandler<GetClarificationBulletinsQuery, List<ClarificationBulletinDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetClarificationBulletinsQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<List<ClarificationBulletinDto>> Handle(
        GetClarificationBulletinsQuery request,
        CancellationToken cancellationToken)
    {
        var bulletins = await _context.ClarificationBulletins
            .AsNoTracking()
            .Include(b => b.Publisher)
            .Include(b => b.Clarifications)
            .Where(b => b.TenderId == request.TenderId)
            .OrderByDescending(b => b.BulletinNumber)
            .ToListAsync(cancellationToken);

        var result = new List<ClarificationBulletinDto>();

        foreach (var bulletin in bulletins)
        {
            var dto = new ClarificationBulletinDto
            {
                Id = bulletin.Id,
                TenderId = bulletin.TenderId,
                BulletinNumber = bulletin.BulletinNumber,
                IssueDate = bulletin.IssueDate,
                Introduction = bulletin.Introduction,
                ClosingNotes = bulletin.ClosingNotes,
                PdfPath = bulletin.PdfPath,
                PublishedBy = bulletin.PublishedBy,
                PublishedByName = $"{bulletin.Publisher.FirstName} {bulletin.Publisher.LastName}",
                PublishedAt = bulletin.PublishedAt,
                QuestionCount = bulletin.Clarifications.Count,
                Questions = bulletin.Clarifications
                    .OrderBy(c => c.ReferenceNumber)
                    .Select(c => new ClarificationBulletinQuestionDto
                    {
                        Id = c.Id,
                        ReferenceNumber = c.ReferenceNumber,
                        Subject = c.Subject,
                        Question = c.Question,
                        Answer = c.Answer ?? string.Empty,
                        RelatedBoqSection = c.RelatedBoqSection,
                        AnsweredAt = c.AnsweredAt
                    })
                    .ToList()
            };

            result.Add(dto);
        }

        return result;
    }
}
