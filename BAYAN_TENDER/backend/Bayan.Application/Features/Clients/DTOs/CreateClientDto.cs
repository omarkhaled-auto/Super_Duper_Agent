namespace Bayan.Application.Features.Clients.DTOs;

/// <summary>
/// Data transfer object for creating a new client.
/// </summary>
public class CreateClientDto
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
}
