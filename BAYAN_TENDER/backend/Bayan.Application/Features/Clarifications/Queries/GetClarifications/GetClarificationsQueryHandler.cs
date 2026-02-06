using AutoMapper;
using AutoMapper.QueryableExtensions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Queries.GetClarifications;

/// <summary>
/// Handler for the GetClarificationsQuery.
/// </summary>
public class GetClarificationsQueryHandler : IRequestHandler<GetClarificationsQuery, PaginatedList<ClarificationDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetClarificationsQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<PaginatedList<ClarificationDto>> Handle(
        GetClarificationsQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.Clarifications
            .AsNoTracking()
            .Where(c => c.TenderId == request.TenderId);

        // Apply filters
        if (request.Status.HasValue)
        {
            query = query.Where(c => c.Status == request.Status.Value);
        }

        if (request.Type.HasValue)
        {
            query = query.Where(c => c.ClarificationType == request.Type.Value);
        }

        if (!string.IsNullOrWhiteSpace(request.Section))
        {
            query = query.Where(c => c.RelatedBoqSection != null &&
                c.RelatedBoqSection.Contains(request.Section));
        }

        if (request.Priority.HasValue)
        {
            query = query.Where(c => c.Priority == request.Priority.Value);
        }

        if (request.BidderId.HasValue)
        {
            query = query.Where(c => c.SubmittedByBidderId == request.BidderId.Value);
        }

        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchLower = request.Search.ToLower();
            query = query.Where(c =>
                c.Subject.ToLower().Contains(searchLower) ||
                c.Question.ToLower().Contains(searchLower) ||
                c.ReferenceNumber.ToLower().Contains(searchLower));
        }

        // Apply sorting
        query = request.SortBy.ToLower() switch
        {
            "referencenumber" => request.SortDescending
                ? query.OrderByDescending(c => c.ReferenceNumber)
                : query.OrderBy(c => c.ReferenceNumber),
            "subject" => request.SortDescending
                ? query.OrderByDescending(c => c.Subject)
                : query.OrderBy(c => c.Subject),
            "status" => request.SortDescending
                ? query.OrderByDescending(c => c.Status)
                : query.OrderBy(c => c.Status),
            "priority" => request.SortDescending
                ? query.OrderByDescending(c => c.Priority)
                : query.OrderBy(c => c.Priority),
            "answeredat" => request.SortDescending
                ? query.OrderByDescending(c => c.AnsweredAt)
                : query.OrderBy(c => c.AnsweredAt),
            "createdat" => request.SortDescending
                ? query.OrderByDescending(c => c.CreatedAt)
                : query.OrderBy(c => c.CreatedAt),
            _ => request.SortDescending
                ? query.OrderByDescending(c => c.SubmittedAt)
                : query.OrderBy(c => c.SubmittedAt)
        };

        var projectedQuery = query.ProjectTo<ClarificationDto>(_mapper.ConfigurationProvider);

        return await PaginatedList<ClarificationDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
