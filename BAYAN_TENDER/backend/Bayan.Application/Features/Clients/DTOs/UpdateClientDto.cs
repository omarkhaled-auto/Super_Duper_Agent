namespace Bayan.Application.Features.Clients.DTOs;

/// <summary>
/// Data transfer object for updating an existing client.
/// </summary>
public class UpdateClientDto
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
    /// Indicates whether the client is currently active.
    /// </summary>
    public bool IsActive { get; set; } = true;
}
