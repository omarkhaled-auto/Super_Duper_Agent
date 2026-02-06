using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bidders.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bidders.Commands.UpdateBidder;

/// <summary>
/// Handler for the UpdateBidderCommand.
/// </summary>
public class UpdateBidderCommandHandler : IRequestHandler<UpdateBidderCommand, BidderDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public UpdateBidderCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<BidderDto?> Handle(
        UpdateBidderCommand request,
        CancellationToken cancellationToken)
    {
        var bidder = await _context.Bidders
            .FirstOrDefaultAsync(b => b.Id == request.Id, cancellationToken);

        if (bidder == null)
        {
            return null;
        }

        bidder.CompanyName = request.CompanyName;
        bidder.CRNumber = request.CRNumber;
        bidder.LicenseNumber = request.LicenseNumber;
        bidder.ContactPerson = request.ContactPerson;
        bidder.Email = request.Email;
        bidder.Phone = request.Phone;
        bidder.TradeSpecialization = request.TradeSpecialization;
        bidder.PrequalificationStatus = request.PrequalificationStatus;
        bidder.IsActive = request.IsActive;
        bidder.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<BidderDto>(bidder);
    }
}
