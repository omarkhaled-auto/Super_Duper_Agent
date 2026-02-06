using Bayan.Application.Common.Interfaces;

namespace Bayan.Infrastructure.Services;

/// <summary>
/// Implementation of datetime service.
/// </summary>
public class DateTimeService : IDateTime
{
    /// <summary>
    /// Gets the current UTC date and time.
    /// </summary>
    public DateTime UtcNow => DateTime.UtcNow;
}
