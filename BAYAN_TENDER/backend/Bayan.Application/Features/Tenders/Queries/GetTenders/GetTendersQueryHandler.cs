using AutoMapper;
using AutoMapper.QueryableExtensions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Tenders.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Queries.GetTenders;

/// <summary>
/// Handler for the GetTendersQuery.
/// </summary>
public class GetTendersQueryHandler : IRequestHandler<GetTendersQuery, PaginatedList<TenderListDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetTendersQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<PaginatedList<TenderListDto>> Handle(
        GetTendersQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.Tenders
            .Include(t => t.Client)
            .Include(t => t.TenderBidders)
            .AsNoTracking();

        // Apply status filter
        if (request.Status.HasValue)
        {
            query = query.Where(t => t.Status == request.Status.Value);
        }

        // Apply client filter
        if (request.ClientId.HasValue)
        {
            query = query.Where(t => t.ClientId == request.ClientId.Value);
        }

        // Apply date range filter
        if (request.DateFrom.HasValue)
        {
            query = query.Where(t => t.CreatedAt >= request.DateFrom.Value);
        }

        if (request.DateTo.HasValue)
        {
            query = query.Where(t => t.CreatedAt <= request.DateTo.Value);
        }

        // Apply tender type filter
        if (request.TenderType.HasValue)
        {
            query = query.Where(t => t.TenderType == request.TenderType.Value);
        }

        // Apply search filter
        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchTerm = request.Search.ToLower();
            query = query.Where(t =>
                t.Title.ToLower().Contains(searchTerm) ||
                t.Reference.ToLower().Contains(searchTerm) ||
                t.Client.Name.ToLower().Contains(searchTerm));
        }

        // Apply sorting
        query = request.SortBy.ToLower() switch
        {
            "title" => request.SortDescending
                ? query.OrderByDescending(t => t.Title)
                : query.OrderBy(t => t.Title),
            "reference" => request.SortDescending
                ? query.OrderByDescending(t => t.Reference)
                : query.OrderBy(t => t.Reference),
            "submissiondeadline" => request.SortDescending
                ? query.OrderByDescending(t => t.SubmissionDeadline)
                : query.OrderBy(t => t.SubmissionDeadline),
            "status" => request.SortDescending
                ? query.OrderByDescending(t => t.Status)
                : query.OrderBy(t => t.Status),
            "clientname" => request.SortDescending
                ? query.OrderByDescending(t => t.Client.Name)
                : query.OrderBy(t => t.Client.Name),
            _ => request.SortDescending
                ? query.OrderByDescending(t => t.CreatedAt)
                : query.OrderBy(t => t.CreatedAt)
        };

        // Project to DTO
        var projectedQuery = query.Select(t => new TenderListDto
        {
            Id = t.Id,
            Title = t.Title,
            Reference = t.Reference,
            ClientName = t.Client.Name,
            TenderType = t.TenderType,
            Status = t.Status,
            BaseCurrency = t.BaseCurrency,
            EstimatedValue = t.EstimatedValue,
            SubmissionDeadline = t.SubmissionDeadline,
            BidderCount = t.TenderBidders.Count,
            DaysRemaining = (int)(t.SubmissionDeadline - DateTime.UtcNow).TotalDays,
            CreatedAt = t.CreatedAt
        });

        return await PaginatedList<TenderListDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
