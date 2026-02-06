using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Queries.GetBids;

/// <summary>
/// Handler for the GetBidsQuery.
/// </summary>
public class GetBidsQueryHandler : IRequestHandler<GetBidsQuery, PaginatedList<BidListDto>>
{
    private readonly IApplicationDbContext _context;

    public GetBidsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<PaginatedList<BidListDto>> Handle(
        GetBidsQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.BidSubmissions
            .Include(b => b.Bidder)
            .Include(b => b.BidDocuments)
            .Where(b => b.TenderId == request.TenderId)
            .AsNoTracking();

        // Apply status filter
        if (request.Status.HasValue)
        {
            query = query.Where(b => b.Status == request.Status.Value);
        }

        // Apply late filter
        if (request.IsLate.HasValue)
        {
            query = query.Where(b => b.IsLate == request.IsLate.Value);
        }

        // Apply late accepted filter
        if (request.LateAccepted.HasValue)
        {
            query = query.Where(b => b.LateAccepted == request.LateAccepted.Value);
        }

        // Apply search filter
        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchTerm = request.Search.ToLower();
            query = query.Where(b =>
                b.Bidder.CompanyName.ToLower().Contains(searchTerm) ||
                b.Bidder.ContactPerson.ToLower().Contains(searchTerm) ||
                b.ReceiptNumber.ToLower().Contains(searchTerm));
        }

        // Apply sorting
        query = request.SortBy.ToLower() switch
        {
            "biddername" => request.SortDescending
                ? query.OrderByDescending(b => b.Bidder.CompanyName)
                : query.OrderBy(b => b.Bidder.CompanyName),
            "status" => request.SortDescending
                ? query.OrderByDescending(b => b.Status)
                : query.OrderBy(b => b.Status),
            "islate" => request.SortDescending
                ? query.OrderByDescending(b => b.IsLate)
                : query.OrderBy(b => b.IsLate),
            "amount" => request.SortDescending
                ? query.OrderByDescending(b => b.NormalizedTotalAmount)
                : query.OrderBy(b => b.NormalizedTotalAmount),
            _ => request.SortDescending
                ? query.OrderByDescending(b => b.SubmissionTime)
                : query.OrderBy(b => b.SubmissionTime)
        };

        // Project to DTO
        var projectedQuery = query.Select(b => new BidListDto
        {
            Id = b.Id,
            TenderId = b.TenderId,
            BidderId = b.BidderId,
            BidderName = b.Bidder.CompanyName,
            ContactPerson = b.Bidder.ContactPerson,
            BidderEmail = b.Bidder.Email,
            SubmissionTime = b.SubmissionTime,
            Status = b.Status,
            IsLate = b.IsLate,
            LateAccepted = b.LateAccepted,
            ReceiptNumber = b.ReceiptNumber,
            // Only show amounts if bids are opened
            NativeCurrency = b.Status == BidSubmissionStatus.Opened ||
                            b.Status == BidSubmissionStatus.Imported ||
                            b.Status == BidSubmissionStatus.Disqualified
                ? b.NativeCurrency : null,
            NativeTotalAmount = b.Status == BidSubmissionStatus.Opened ||
                               b.Status == BidSubmissionStatus.Imported ||
                               b.Status == BidSubmissionStatus.Disqualified
                ? b.NativeTotalAmount : null,
            NormalizedTotalAmount = b.Status == BidSubmissionStatus.Opened ||
                                   b.Status == BidSubmissionStatus.Imported ||
                                   b.Status == BidSubmissionStatus.Disqualified
                ? b.NormalizedTotalAmount : null,
            CommercialFileCount = b.BidDocuments.Count(d => d.DocumentType == BidDocumentType.PricedBOQ),
            TechnicalFileCount = b.BidDocuments.Count(d => d.DocumentType != BidDocumentType.PricedBOQ),
            TotalFileCount = b.BidDocuments.Count,
            ImportStatus = b.ImportStatus
        });

        return await PaginatedList<BidListDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
