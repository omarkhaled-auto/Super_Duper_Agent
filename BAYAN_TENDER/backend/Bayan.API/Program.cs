using Bayan.API.Middleware;
using Bayan.Application;
using Bayan.Infrastructure;
using Bayan.Infrastructure.Jobs;
using Hangfire;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.OpenApi.Models;
using Serilog;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();

// Add Application services (MediatR, AutoMapper, FluentValidation)
builder.Services.AddApplicationServices();

// Add Infrastructure services (EF Core, JWT, Identity, Health Checks)
builder.Services.AddInfrastructureServices(builder.Configuration);

// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "Bayan Tender API",
        Version = "v1",
        Description = "API for Bayan Tender Management System - A comprehensive platform for managing tenders, bids, and procurement workflows.",
        Contact = new OpenApiContact
        {
            Name = "Bayan Support",
            Email = "support@bayan.com",
            Url = new Uri("https://bayan.com/support")
        },
        License = new OpenApiLicense
        {
            Name = "Proprietary",
            Url = new Uri("https://bayan.com/license")
        }
    });

    // Add JWT Bearer authentication to Swagger
    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        In = ParameterLocation.Header,
        Description = "Enter your JWT token in the format: Bearer {token}"
    });

    options.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });

    // Include XML comments from the API project
    var xmlFilename = $"{System.Reflection.Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xmlFilename);
    if (File.Exists(xmlPath))
    {
        options.IncludeXmlComments(xmlPath);
    }

    // Enable annotations
    options.EnableAnnotations();
});

// Add CORS for frontend with security-conscious configuration
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        var allowedOrigins = builder.Configuration.GetSection("AllowedOrigins").Get<string[]>()
            ?? new[] { "http://localhost:4200", "http://localhost:3000" };

        policy
            .WithOrigins(allowedOrigins)
            .WithMethods("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
            .WithHeaders(
                "Authorization",
                "Content-Type",
                "Accept",
                "Accept-Language",
                "X-Requested-With",
                "X-Correlation-Id")
            .WithExposedHeaders(
                "Content-Disposition",
                "X-Pagination",
                "X-Total-Count")
            .AllowCredentials()
            .SetPreflightMaxAge(TimeSpan.FromMinutes(10));
    });
});

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .WriteTo.Console()
    .WriteTo.File("logs/bayan-.log", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

var app = builder.Build();

// Initialize database (apply migrations and seed data in Development)
if (app.Environment.IsDevelopment())
{
    try
    {
        Log.Information("Initializing database...");
        await app.InitializeDatabaseAsync();
        Log.Information("Database initialization completed");
    }
    catch (Exception ex)
    {
        Log.Error(ex, "Database initialization failed. The application will continue but some features may not work.");
    }
}

// Use exception handling middleware (should be first in the pipeline)
app.UseExceptionHandling();

// Add security headers middleware
app.UseSecurityHeaders();

// Add rate limiting middleware (reads from RateLimiting config section)
var rateLimitConfig = builder.Configuration.GetSection("RateLimiting");
app.UseRateLimiting(options =>
{
    options.RequestsPerMinute = rateLimitConfig.GetValue<int?>("PermitLimit") ?? 100;
    options.Enabled = rateLimitConfig.GetValue<bool?>("EnableRateLimiting") ?? !app.Environment.IsDevelopment();
});

// Add request size limiting
app.UseRequestSizeLimit(options =>
{
    options.MaxRequestSizeBytes = 10 * 1024 * 1024; // 10 MB for regular requests
    options.MaxFileUploadSizeBytes = 50 * 1024 * 1024; // 50 MB for file uploads
    options.Enabled = true;
});

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "Bayan Tender API v1");
        c.RoutePrefix = string.Empty; // Set Swagger UI at the app root
        c.DisplayRequestDuration();
        c.EnableDeepLinking();
        c.EnableFilter();
        c.DocExpansion(Swashbuckle.AspNetCore.SwaggerUI.DocExpansion.None);
    });
}

app.UseHttpsRedirection();

app.UseCors("AllowFrontend");

app.UseAuthentication();
app.UseAuthorization();

app.UseRequestLogging();
app.UseAuditLogging();

app.MapControllers();

// Map health check endpoints
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = HealthCheckResponseWriter.WriteResponse
});

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("db"),
    ResponseWriter = HealthCheckResponseWriter.WriteResponse
});

app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false // Always returns healthy if the app is running
});

// Configure Hangfire dashboard and register recurring jobs
var hangfireSettings = builder.Configuration.GetSection(HangfireSettings.SectionName).Get<HangfireSettings>();
if (hangfireSettings?.Enabled == true)
{
    // Configure Hangfire dashboard with authorization
    var dashboardOptions = new DashboardOptions
    {
        DashboardTitle = "Bayan Background Jobs",
        DisplayStorageConnectionString = false,
        StatsPollingInterval = 10000 // 10 seconds
    };

    if (app.Environment.IsDevelopment())
    {
        // In development, allow local access only
        dashboardOptions.Authorization = new[] { new HangfireLocalAuthorizationFilter() };
    }
    else
    {
        // In production, require authentication
        dashboardOptions.Authorization = new[] { new HangfireDashboardAuthorizationFilter(hangfireSettings.AllowedRoles) };
    }

    app.UseHangfireDashboard(hangfireSettings.DashboardPath, dashboardOptions);

    // Register recurring jobs
    using (var scope = app.Services.CreateScope())
    {
        var backgroundJobsService = scope.ServiceProvider.GetService<IBackgroundJobsService>();
        backgroundJobsService?.RegisterRecurringJobs();

        // Run cache warmup job immediately on startup
        var cacheWarmupJob = scope.ServiceProvider.GetService<CacheWarmupJob>();
        if (cacheWarmupJob != null)
        {
            try
            {
                Log.Information("Running initial cache warmup...");
                await cacheWarmupJob.ExecuteAsync();
                Log.Information("Initial cache warmup completed");
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Initial cache warmup failed, but application will continue");
            }
        }
    }

    Log.Information("Hangfire dashboard available at {Path}", hangfireSettings.DashboardPath);
}

try
{
    Log.Information("Starting Bayan Tender API");
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}

// Make Program class accessible to WebApplicationFactory in test projects
public partial class Program { }

/// <summary>
/// Custom health check response writer that returns detailed JSON.
/// </summary>
public static class HealthCheckResponseWriter
{
    public static Task WriteResponse(HttpContext context, HealthReport report)
    {
        context.Response.ContentType = "application/json";

        var response = new
        {
            status = report.Status.ToString(),
            totalDuration = report.TotalDuration.TotalMilliseconds,
            timestamp = DateTime.UtcNow,
            checks = report.Entries.Select(entry => new
            {
                name = entry.Key,
                status = entry.Value.Status.ToString(),
                duration = entry.Value.Duration.TotalMilliseconds,
                description = entry.Value.Description,
                exception = entry.Value.Exception?.Message,
                data = entry.Value.Data
            })
        };

        var options = new JsonSerializerOptions
        {
            WriteIndented = true,
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };

        return context.Response.WriteAsJsonAsync(response, options);
    }
}
