using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bidders.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Bidders.Commands.CreateBidder;

/// <summary>
/// Handler for the CreateBidderCommand.
/// </summary>
public class CreateBidderCommandHandler : IRequestHandler<CreateBidderCommand, BidderDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public CreateBidderCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<BidderDto> Handle(
        CreateBidderCommand request,
        CancellationToken cancellationToken)
    {
        var bidder = new Bidder
        {
            Id = Guid.NewGuid(),
            CompanyName = request.CompanyName,
            CRNumber = request.CRNumber,
            LicenseNumber = request.LicenseNumber,
            ContactPerson = request.ContactPerson,
            Email = request.Email,
            Phone = request.Phone,
            TradeSpecialization = request.TradeSpecialization,
            PrequalificationStatus = PrequalificationStatus.Pending,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        _context.Bidders.Add(bidder);
        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<BidderDto>(bidder);
    }
}
