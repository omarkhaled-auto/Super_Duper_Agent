using Hangfire;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Jobs;

/// <summary>
/// Service for registering and managing background jobs.
/// </summary>
public interface IBackgroundJobsService
{
    /// <summary>
    /// Registers all recurring jobs.
    /// </summary>
    void RegisterRecurringJobs();

    /// <summary>
    /// Enqueues a job to create vendor pricing snapshot.
    /// </summary>
    /// <param name="bidSubmissionId">The bid submission ID.</param>
    void EnqueueVendorPricingSnapshot(Guid bidSubmissionId);

    /// <summary>
    /// Enqueues a job to create vendor pricing snapshots for all bids in a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    void EnqueueVendorPricingSnapshotForTender(Guid tenderId);
}

/// <summary>
/// Implementation of background jobs service using Hangfire.
/// </summary>
public class BackgroundJobsService : IBackgroundJobsService
{
    private readonly IRecurringJobManager _recurringJobManager;
    private readonly IBackgroundJobClient _backgroundJobClient;
    private readonly ILogger<BackgroundJobsService> _logger;

    public BackgroundJobsService(
        IRecurringJobManager recurringJobManager,
        IBackgroundJobClient backgroundJobClient,
        ILogger<BackgroundJobsService> logger)
    {
        _recurringJobManager = recurringJobManager;
        _backgroundJobClient = backgroundJobClient;
        _logger = logger;
    }

    /// <inheritdoc />
    public void RegisterRecurringJobs()
    {
        _logger.LogInformation("Registering recurring background jobs...");

        // Deadline Reminder Job - Runs daily at 8:00 AM UTC
        _recurringJobManager.AddOrUpdate<DeadlineReminderJob>(
            "deadline-reminder",
            job => job.ExecuteAsync(),
            "0 8 * * *", // Cron expression: At 08:00 every day
            new RecurringJobOptions
            {
                TimeZone = TimeZoneInfo.Utc
            });
        _logger.LogDebug("Registered deadline reminder job (daily at 8:00 AM UTC)");

        // NDA Expiry Check Job - Runs daily at 1:00 AM UTC
        _recurringJobManager.AddOrUpdate<NdaExpiryCheckJob>(
            "nda-expiry-check",
            job => job.ExecuteAsync(),
            "0 1 * * *", // Cron expression: At 01:00 every day
            new RecurringJobOptions
            {
                TimeZone = TimeZoneInfo.Utc
            });
        _logger.LogDebug("Registered NDA expiry check job (daily at 1:00 AM UTC)");

        // Cache Warmup Job - Runs every 30 minutes
        _recurringJobManager.AddOrUpdate<CacheWarmupJob>(
            "cache-warmup",
            job => job.ExecuteAsync(),
            "*/30 * * * *", // Cron expression: Every 30 minutes
            new RecurringJobOptions
            {
                TimeZone = TimeZoneInfo.Utc
            });
        _logger.LogDebug("Registered cache warmup job (every 30 minutes)");

        _logger.LogInformation("All recurring background jobs registered successfully");
    }

    /// <inheritdoc />
    public void EnqueueVendorPricingSnapshot(Guid bidSubmissionId)
    {
        _logger.LogInformation(
            "Enqueueing vendor pricing snapshot job for bid submission {BidSubmissionId}",
            bidSubmissionId);

        _backgroundJobClient.Enqueue<VendorPricingSnapshotJob>(
            job => job.ExecuteAsync(bidSubmissionId));
    }

    /// <inheritdoc />
    public void EnqueueVendorPricingSnapshotForTender(Guid tenderId)
    {
        _logger.LogInformation(
            "Enqueueing vendor pricing snapshot job for tender {TenderId}",
            tenderId);

        _backgroundJobClient.Enqueue<VendorPricingSnapshotJob>(
            job => job.ExecuteForTenderAsync(tenderId));
    }
}
