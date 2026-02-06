using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Addenda.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Addenda.Commands.CreateAddendum;

/// <summary>
/// Handler for the CreateAddendumCommand.
/// </summary>
public class CreateAddendumCommandHandler : IRequestHandler<CreateAddendumCommand, AddendumDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public CreateAddendumCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<AddendumDto> Handle(
        CreateAddendumCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists and is in a valid state for addenda
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        // Ensure tender is in a state where addenda can be created
        if (tender.Status != TenderStatus.Active)
        {
            throw new InvalidOperationException(
                $"Cannot create addendum for tender in '{tender.Status}' status. " +
                "Tender must be in Active status.");
        }

        // Get the next addendum number
        var maxAddendumNumber = await _context.Addenda
            .Where(a => a.TenderId == request.TenderId)
            .MaxAsync(a => (int?)a.AddendumNumber, cancellationToken) ?? 0;

        var addendum = new Addendum
        {
            Id = Guid.NewGuid(),
            TenderId = request.TenderId,
            AddendumNumber = maxAddendumNumber + 1,
            IssueDate = DateTime.UtcNow,
            Summary = request.Summary,
            ExtendsDeadline = request.ExtendsDeadline,
            NewDeadline = request.ExtendsDeadline ? request.NewDeadline : null,
            Status = AddendumStatus.Draft,
            CreatedAt = DateTime.UtcNow
        };

        _context.Addenda.Add(addendum);
        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<AddendumDto>(addendum);
    }
}
