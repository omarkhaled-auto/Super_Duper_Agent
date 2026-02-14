namespace Bayan.Infrastructure.Jobs;

/// <summary>
/// Settings for Hangfire configuration.
/// </summary>
public class HangfireSettings
{
    /// <summary>
    /// Configuration section name.
    /// </summary>
    public const string SectionName = "Hangfire";

    /// <summary>
    /// Whether Hangfire is enabled.
    /// </summary>
    public bool Enabled { get; set; } = true;

    /// <summary>
    /// Dashboard path (e.g., "/hangfire").
    /// </summary>
    public string DashboardPath { get; set; } = "/hangfire";

    /// <summary>
    /// Number of workers to use.
    /// </summary>
    public int WorkerCount { get; set; } = 5;

    /// <summary>
    /// Schema name for PostgreSQL storage.
    /// </summary>
    public string SchemaName { get; set; } = "hangfire";

    /// <summary>
    /// Whether to allow access to the dashboard only for authenticated users.
    /// </summary>
    public bool RequireAuthentication { get; set; } = true;

    /// <summary>
    /// Roles that can access the dashboard.
    /// </summary>
    public string[] AllowedRoles { get; set; } = { "Admin", "TenderManager" };
}
