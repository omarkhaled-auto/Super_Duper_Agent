using Bayan.Application.Features.Clients.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clients.Commands.CreateClient;

/// <summary>
/// Command for creating a new client.
/// </summary>
public class CreateClientCommand : IRequest<ClientDto>
{
    /// <summary>
    /// Name of the client organization.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Name of the primary contact person.
    /// </summary>
    public string? ContactPerson { get; set; }

    /// <summary>
    /// Email address for the client.
    /// </summary>
    public string? Email { get; set; }

    /// <summary>
    /// Phone number for the client.
    /// </summary>
    public string? Phone { get; set; }

    /// <summary>
    /// Physical address of the client.
    /// </summary>
    public string? Address { get; set; }

    /// <summary>
    /// City where the client is located.
    /// </summary>
    public string? City { get; set; }

    /// <summary>
    /// Country where the client is located.
    /// </summary>
    public string? Country { get; set; }

    /// <summary>
    /// Commercial Registration Number.
    /// </summary>
    public string? CRNumber { get; set; }

    /// <summary>
    /// VAT registration number.
    /// </summary>
    public string? VatNumber { get; set; }

    /// <summary>
    /// Contact person's email address.
    /// </summary>
    public string? ContactEmail { get; set; }

    /// <summary>
    /// Contact person's phone number.
    /// </summary>
    public string? ContactPhone { get; set; }
}
