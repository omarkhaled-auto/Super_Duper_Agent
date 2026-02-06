using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clients.DTOs;
using Bayan.Domain.Entities;
using MediatR;

namespace Bayan.Application.Features.Clients.Commands.CreateClient;

/// <summary>
/// Handler for the CreateClientCommand.
/// </summary>
public class CreateClientCommandHandler : IRequestHandler<CreateClientCommand, ClientDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public CreateClientCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClientDto> Handle(
        CreateClientCommand request,
        CancellationToken cancellationToken)
    {
        var client = new Client
        {
            Id = Guid.NewGuid(),
            Name = request.Name,
            ContactPerson = request.ContactPerson,
            Email = request.Email,
            Phone = request.Phone,
            Address = request.Address,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        _context.Clients.Add(client);
        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<ClientDto>(client);
    }
}
