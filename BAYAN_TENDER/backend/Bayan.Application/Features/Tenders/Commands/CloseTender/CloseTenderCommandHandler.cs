using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.CloseTender;

/// <summary>
/// Handler for the CloseTenderCommand.
/// Transitions a tender from Active to Evaluation status.
/// </summary>
public class CloseTenderCommandHandler : IRequestHandler<CloseTenderCommand, TenderDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly ICurrentUserService _currentUserService;

    public CloseTenderCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _mapper = mapper;
        _currentUserService = currentUserService;
    }

    public async Task<TenderDto?> Handle(
        CloseTenderCommand request,
        CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .Include(t => t.Client)
            .Include(t => t.TenderBidders)
            .FirstOrDefaultAsync(t => t.Id == request.Id, cancellationToken);

        if (tender == null)
        {
            return null;
        }

        // Transition to Evaluation status (close bidding)
        tender.Status = TenderStatus.Evaluation;
        tender.LastModifiedBy = _currentUserService.UserId;
        tender.LastModifiedAt = DateTime.UtcNow;
        tender.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return new TenderDto
        {
            Id = tender.Id,
            Title = tender.Title,
            Reference = tender.Reference,
            ClientId = tender.ClientId,
            ClientName = tender.Client.Name,
            TenderType = tender.TenderType,
            BaseCurrency = tender.BaseCurrency,
            Status = tender.Status,
            SubmissionDeadline = tender.SubmissionDeadline,
            BidderCount = tender.TenderBidders.Count,
            BidCount = 0,
            CreatedAt = tender.CreatedAt
        };
    }
}
