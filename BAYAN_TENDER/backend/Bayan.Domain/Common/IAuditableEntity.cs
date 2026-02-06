namespace Bayan.Domain.Common;

/// <summary>
/// Interface for entities that track audit information.
/// </summary>
public interface IAuditableEntity
{
    /// <summary>
    /// Identifier of the user who created the entity.
    /// </summary>
    Guid? CreatedBy { get; set; }

    /// <summary>
    /// Timestamp when the entity was created.
    /// </summary>
    DateTime CreatedAt { get; set; }

    /// <summary>
    /// Identifier of the user who last modified the entity.
    /// </summary>
    Guid? LastModifiedBy { get; set; }

    /// <summary>
    /// Timestamp when the entity was last modified.
    /// </summary>
    DateTime? LastModifiedAt { get; set; }
}
