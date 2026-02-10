using System.Text;
using Bayan.Application.Common.Interfaces;
using Bayan.Infrastructure.Caching;
using Bayan.Infrastructure.Data;
using Bayan.Infrastructure.Email;
using Bayan.Infrastructure.Excel;
using Bayan.Infrastructure.FileStorage;
using Bayan.Infrastructure.Identity;
using Bayan.Infrastructure.Matching;
using Bayan.Infrastructure.Jobs;
using Bayan.Infrastructure.Pdf;
using Bayan.Infrastructure.Persistence;
using Bayan.Infrastructure.Services;
using Hangfire;
using Hangfire.PostgreSql;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.IdentityModel.Tokens;
using Minio;
using StackExchange.Redis;

namespace Bayan.Infrastructure;

/// <summary>
/// Extension methods for registering infrastructure services.
/// </summary>
public static class DependencyInjection
{
    /// <summary>
    /// Adds infrastructure layer services to the dependency injection container.
    /// </summary>
    public static IServiceCollection AddInfrastructureServices(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var connectionString = configuration.GetConnectionString("DefaultConnection");

        // Configure PostgreSQL with connection resiliency
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseNpgsql(connectionString,
                builder =>
                {
                    builder.MigrationsAssembly(typeof(ApplicationDbContext).Assembly.FullName);
                    builder.EnableRetryOnFailure(
                        maxRetryCount: 5,
                        maxRetryDelay: TimeSpan.FromSeconds(30),
                        errorCodesToAdd: null);
                }));

        services.AddScoped<IApplicationDbContext>(provider =>
            provider.GetRequiredService<ApplicationDbContext>());

        // Register database seeder
        services.AddScoped<ApplicationDbContextSeed>();

        // Configure JWT settings
        services.Configure<JwtSettings>(configuration.GetSection(JwtSettings.SectionName));

        // Configure JWT Authentication
        var jwtSettings = configuration.GetSection(JwtSettings.SectionName).Get<JwtSettings>();
        if (jwtSettings != null)
        {
            services.AddAuthentication(options =>
            {
                options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
                options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
            })
            .AddJwtBearer(options =>
            {
                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuerSigningKey = true,
                    IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSettings.SecretKey)),
                    ValidateIssuer = true,
                    ValidIssuer = jwtSettings.Issuer,
                    ValidateAudience = true,
                    ValidAudience = jwtSettings.Audience,
                    ValidateLifetime = true,
                    ClockSkew = TimeSpan.Zero
                };
            });
        }

        // Add health checks for database
        services.AddHealthChecks()
            .AddNpgSql(connectionString ?? string.Empty, name: "postgresql", tags: new[] { "db", "sql", "postgresql" });

        // Register services
        services.AddHttpContextAccessor();
        services.AddScoped<ICurrentUserService, CurrentUserService>();
        services.AddScoped<IDateTime, DateTimeService>();
        services.AddScoped<IPasswordHasher, PasswordHasher>();
        services.AddScoped<IJwtTokenService, JwtTokenService>();

        // Configure Email settings
        services.Configure<SmtpSettings>(configuration.GetSection(SmtpSettings.SectionName));
        services.AddSingleton<IEmailTemplateService, EmailTemplateService>();
        services.AddScoped<IEmailService, EmailService>();

        // Register Excel services
        services.AddScoped<ITemplateExportService, TemplateExportService>();
        services.AddScoped<IExcelService, ExcelService>();
        services.AddScoped<IComparableSheetExportService, ComparableSheetExportService>();

        // Register Dapper context for raw SQL queries
        services.AddScoped<IDapperContext, DapperContext>();

        // Register PDF services
        services.AddScoped<IPdfService, PdfService>();

        // Register Fuzzy Matching service
        services.AddScoped<IFuzzyMatchingService, FuzzyMatchingService>();

        // Register UOM Conversion service
        services.AddMemoryCache();
        services.AddScoped<IUomConversionService, UomConversionService>();

        // Configure MinIO settings
        services.Configure<MinioSettings>(configuration.GetSection(MinioSettings.SectionName));
        var minioSettings = configuration.GetSection(MinioSettings.SectionName).Get<MinioSettings>();

        if (minioSettings != null && !string.IsNullOrWhiteSpace(minioSettings.Endpoint))
        {
            services.AddSingleton<IMinioClient>(sp =>
            {
                var client = new MinioClient()
                    .WithEndpoint(minioSettings.Endpoint)
                    .WithCredentials(minioSettings.AccessKey, minioSettings.SecretKey);

                if (minioSettings.UseSSL)
                {
                    client = client.WithSSL();
                }

                if (!string.IsNullOrWhiteSpace(minioSettings.Region))
                {
                    client = client.WithRegion(minioSettings.Region);
                }

                return client.Build();
            });

            services.AddScoped<IFileStorageService, MinioFileStorageService>();
        }

        // Configure Redis caching
        services.Configure<RedisSettings>(configuration.GetSection(RedisSettings.SectionName));
        var redisSettings = configuration.GetSection(RedisSettings.SectionName).Get<RedisSettings>();

        if (redisSettings != null && redisSettings.Enabled)
        {
            try
            {
                var redisConfig = ConfigurationOptions.Parse(redisSettings.ConnectionString);
                redisConfig.ConnectTimeout = redisSettings.ConnectTimeout;
                redisConfig.SyncTimeout = redisSettings.SyncTimeout;
                redisConfig.AbortOnConnectFail = redisSettings.AbortOnConnectFail;

                services.AddSingleton<IConnectionMultiplexer>(sp =>
                {
                    var logger = sp.GetRequiredService<ILogger<RedisCacheService>>();
                    try
                    {
                        var connection = ConnectionMultiplexer.Connect(redisConfig);
                        logger.LogInformation("Successfully connected to Redis at {Endpoint}", redisSettings.ConnectionString);
                        return connection;
                    }
                    catch (Exception ex)
                    {
                        logger.LogWarning(ex, "Failed to connect to Redis. Using no-op cache service.");
                        throw;
                    }
                });

                services.AddSingleton<ICacheService, RedisCacheService>();

                // Redis health is implicitly checked via ConnectionMultiplexer
            }
            catch (Exception ex)
            {
                // If Redis configuration fails, log warning and use no-op cache
                using var sp = services.BuildServiceProvider();
                var logger = sp.GetService<ILogger<RedisCacheService>>();
                logger?.LogWarning(ex, "Redis configuration failed. Falling back to no-op cache service");
                services.AddSingleton<ICacheService, NoOpCacheService>();
            }
        }
        else
        {
            // Redis disabled or not configured - use no-op cache
            services.AddSingleton<ICacheService, NoOpCacheService>();
        }

        // Configure Hangfire
        services.Configure<HangfireSettings>(configuration.GetSection(HangfireSettings.SectionName));
        var hangfireSettings = configuration.GetSection(HangfireSettings.SectionName).Get<HangfireSettings>();

        if (hangfireSettings?.Enabled == true && !string.IsNullOrEmpty(connectionString))
        {
            services.AddHangfire(config =>
            {
                config.SetDataCompatibilityLevel(CompatibilityLevel.Version_180)
                    .UseSimpleAssemblyNameTypeSerializer()
                    .UseRecommendedSerializerSettings()
                    .UsePostgreSqlStorage(options =>
                        options.UseNpgsqlConnection(connectionString), new PostgreSqlStorageOptions
                        {
                            SchemaName = hangfireSettings.SchemaName,
                            QueuePollInterval = TimeSpan.FromSeconds(15),
                            JobExpirationCheckInterval = TimeSpan.FromHours(1),
                            CountersAggregateInterval = TimeSpan.FromMinutes(5),
                            PrepareSchemaIfNecessary = true,
                            TransactionSynchronisationTimeout = TimeSpan.FromMinutes(5)
                        });
            });

            services.AddHangfireServer(options =>
            {
                options.WorkerCount = hangfireSettings.WorkerCount;
                options.Queues = new[] { "default", "critical", "low" };
            });

            // Register background jobs
            services.AddScoped<DeadlineReminderJob>();
            services.AddScoped<NdaExpiryCheckJob>();
            services.AddScoped<CacheWarmupJob>();
            services.AddScoped<VendorPricingSnapshotJob>();
            services.AddScoped<IBackgroundJobsService, BackgroundJobsService>();
        }

        return services;
    }

    /// <summary>
    /// Initializes the database by applying migrations and seeding data.
    /// Call this method during application startup in Development environment.
    /// </summary>
    /// <param name="host">The web application host</param>
    /// <returns>A task representing the asynchronous operation</returns>
    public static async Task InitializeDatabaseAsync(this IHost host)
    {
        using var scope = host.Services.CreateScope();
        var services = scope.ServiceProvider;
        var logger = services.GetRequiredService<ILogger<ApplicationDbContext>>();
        var environment = services.GetRequiredService<IHostEnvironment>();

        try
        {
            var context = services.GetRequiredService<ApplicationDbContext>();

            // Apply pending migrations
            logger.LogInformation("Checking for pending database migrations...");
            var pendingMigrations = await context.Database.GetPendingMigrationsAsync();

            if (pendingMigrations.Any())
            {
                logger.LogInformation("Applying {Count} pending migrations: {Migrations}",
                    pendingMigrations.Count(),
                    string.Join(", ", pendingMigrations));

                await context.Database.MigrateAsync();
                logger.LogInformation("Database migrations applied successfully");
            }
            else
            {
                logger.LogInformation("Database is up to date, no migrations to apply");
            }

            // Seed data only in Development environment
            if (environment.IsDevelopment())
            {
                logger.LogInformation("Development environment detected, seeding database...");
                var seeder = services.GetRequiredService<ApplicationDbContextSeed>();
                await seeder.SeedAllAsync();
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "An error occurred while initializing the database");
            throw;
        }
    }

    /// <summary>
    /// Ensures the database is created and migrations are applied.
    /// Use this for quick setup without full seeding.
    /// </summary>
    /// <param name="host">The web application host</param>
    /// <returns>A task representing the asynchronous operation</returns>
    public static async Task EnsureDatabaseCreatedAsync(this IHost host)
    {
        using var scope = host.Services.CreateScope();
        var services = scope.ServiceProvider;
        var logger = services.GetRequiredService<ILogger<ApplicationDbContext>>();

        try
        {
            var context = services.GetRequiredService<ApplicationDbContext>();

            logger.LogInformation("Ensuring database exists...");
            await context.Database.EnsureCreatedAsync();
            logger.LogInformation("Database existence verified");
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "An error occurred while ensuring the database exists");
            throw;
        }
    }
}
