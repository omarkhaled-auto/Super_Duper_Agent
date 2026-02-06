namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for datetime service to enable testing.
/// </summary>
public interface IDateTime
{
    /// <summary>
    /// Gets the current UTC date and time.
    /// </summary>
    DateTime UtcNow { get; }
}
