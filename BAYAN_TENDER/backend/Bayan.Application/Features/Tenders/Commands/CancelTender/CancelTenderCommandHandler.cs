using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.CancelTender;

/// <summary>
/// Handler for the CancelTenderCommand.
/// </summary>
public class CancelTenderCommandHandler : IRequestHandler<CancelTenderCommand, TenderDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly ICurrentUserService _currentUserService;

    public CancelTenderCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _mapper = mapper;
        _currentUserService = currentUserService;
    }

    public async Task<TenderDto?> Handle(
        CancelTenderCommand request,
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

        // Update tender status to Cancelled
        tender.Status = TenderStatus.Cancelled;
        tender.LastModifiedBy = _currentUserService.UserId;
        tender.LastModifiedAt = DateTime.UtcNow;
        tender.UpdatedAt = DateTime.UtcNow;

        // Note: Cancellation reason could be stored in a separate AuditLog or TenderHistory table
        // For now, we'll just update the status

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
