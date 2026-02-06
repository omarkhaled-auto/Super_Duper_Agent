using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clients.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clients.Commands.UpdateClient;

/// <summary>
/// Handler for the UpdateClientCommand.
/// </summary>
public class UpdateClientCommandHandler : IRequestHandler<UpdateClientCommand, ClientDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public UpdateClientCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClientDto?> Handle(
        UpdateClientCommand request,
        CancellationToken cancellationToken)
    {
        var client = await _context.Clients
            .FirstOrDefaultAsync(c => c.Id == request.Id, cancellationToken);

        if (client == null)
        {
            return null;
        }

        client.Name = request.Name;
        client.ContactPerson = request.ContactPerson;
        client.Email = request.Email;
        client.Phone = request.Phone;
        client.Address = request.Address;
        client.IsActive = request.IsActive;
        client.UpdatedAt = DateTime.UtcNow;
        client.LastModifiedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<ClientDto>(client);
    }
}
