namespace Bayan.Application.Features.Addenda.DTOs;

/// <summary>
/// Data transfer object for creating a new addendum.
/// </summary>
public class CreateAddendumDto
{
    /// <summary>
    /// Summary of changes in this addendum.
    /// </summary>
    public string Summary { get; set; } = string.Empty;

    /// <summary>
    /// Whether this addendum extends the submission deadline.
    /// </summary>
    public bool ExtendsDeadline { get; set; }

    /// <summary>
    /// New submission deadline (required if ExtendsDeadline is true).
    /// </summary>
    public DateTime? NewDeadline { get; set; }
}
