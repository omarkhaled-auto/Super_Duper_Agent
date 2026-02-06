using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a client entity in the system.
/// </summary>
public class Client : BaseEntity, IAuditableEntity
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

    // IAuditableEntity implementation
    public Guid? CreatedBy { get; set; }
    public new DateTime CreatedAt { get; set; }
    public Guid? LastModifiedBy { get; set; }
    public DateTime? LastModifiedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tenders associated with this client.
    /// </summary>
    public virtual ICollection<Tender> Tenders { get; set; } = new List<Tender>();
}
