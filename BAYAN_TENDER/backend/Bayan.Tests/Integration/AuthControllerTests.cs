using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Auth.DTOs;
using Bayan.Domain.Common;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using Bayan.Infrastructure.Identity;
using FluentAssertions;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Moq;

namespace Bayan.Tests.Integration;

/// <summary>
/// Integration tests for AuthController endpoints.
/// </summary>
public class AuthControllerTests : IClassFixture<BayanWebApplicationFactory>, IAsyncLifetime
{
    private readonly BayanWebApplicationFactory _factory;
    private readonly HttpClient _client;
    private readonly JsonSerializerOptions _jsonOptions;

    public AuthControllerTests(BayanWebApplicationFactory factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        };
    }

    public async Task InitializeAsync()
    {
        await _factory.ResetDatabaseAsync();
    }

    public Task DisposeAsync() => Task.CompletedTask;

    [Fact]
    public async Task Login_WithValidCredentials_ReturnsTokens()
    {
        // Arrange
        var email = "test@example.com";
        var password = "TestPassword123!";
        await _factory.SeedUserAsync(email, password);

        var loginRequest = new
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/auth/login", loginRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var content = await response.Content.ReadFromJsonAsync<LoginResponseDto>(_jsonOptions);
        content.Should().NotBeNull();
        content!.AccessToken.Should().NotBeNullOrEmpty();
        content.RefreshToken.Should().NotBeNullOrEmpty();
        content.TokenType.Should().Be("Bearer");
        content.User.Should().NotBeNull();
        content.User.Email.Should().Be(email);
    }

    [Fact]
    public async Task Login_WithInvalidPassword_ReturnsUnauthorized()
    {
        // Arrange
        var email = "test@example.com";
        await _factory.SeedUserAsync(email, "CorrectPassword123!");

        var loginRequest = new
        {
            Email = email,
            Password = "WrongPassword123!",
            RememberMe = false
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/auth/login", loginRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task Login_WithNonExistentUser_ReturnsUnauthorized()
    {
        // Arrange
        var loginRequest = new
        {
            Email = "nonexistent@example.com",
            Password = "AnyPassword123!",
            RememberMe = false
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/auth/login", loginRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task RefreshToken_WithValidToken_ReturnsNewTokens()
    {
        // Arrange
        var email = "test@example.com";
        var password = "TestPassword123!";
        await _factory.SeedUserAsync(email, password);

        // First, login to get tokens
        var loginRequest = new
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        var loginResponse = await _client.PostAsJsonAsync("/api/auth/login", loginRequest);
        var loginContent = await loginResponse.Content.ReadFromJsonAsync<LoginResponseDto>(_jsonOptions);

        // Use refresh token to get new tokens
        var refreshRequest = new
        {
            RefreshToken = loginContent!.RefreshToken
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/auth/refresh-token", refreshRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var content = await response.Content.ReadFromJsonAsync<TokenDto>(_jsonOptions);
        content.Should().NotBeNull();
        content!.AccessToken.Should().NotBeNullOrEmpty();
        content.RefreshToken.Should().NotBeNullOrEmpty();
        content.TokenType.Should().Be("Bearer");
    }

    [Fact]
    public async Task RefreshToken_WithInvalidToken_ReturnsUnauthorized()
    {
        // Arrange
        var refreshRequest = new
        {
            RefreshToken = "invalid-refresh-token"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/auth/refresh-token", refreshRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task GetCurrentUser_WithoutAuthentication_ReturnsUnauthorized()
    {
        // Act
        var response = await _client.GetAsync("/api/auth/me");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task GetCurrentUser_WithValidToken_ReturnsUserInfo()
    {
        // Arrange
        var email = "test@example.com";
        var password = "TestPassword123!";
        await _factory.SeedUserAsync(email, password);

        // Login to get access token
        var loginRequest = new
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        var loginResponse = await _client.PostAsJsonAsync("/api/auth/login", loginRequest);
        var loginContent = await loginResponse.Content.ReadFromJsonAsync<LoginResponseDto>(_jsonOptions);

        // Create a new client with the authorization header
        var authenticatedClient = _factory.CreateClient();
        authenticatedClient.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", loginContent!.AccessToken);

        // Act
        var response = await authenticatedClient.GetAsync("/api/auth/me");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var content = await response.Content.ReadFromJsonAsync<UserDto>(_jsonOptions);
        content.Should().NotBeNull();
        content!.Email.Should().Be(email);
    }

    [Fact]
    public async Task GetCurrentUser_WithExpiredToken_ReturnsUnauthorized()
    {
        // Arrange - using an invalid/expired token format
        var authenticatedClient = _factory.CreateClient();
        authenticatedClient.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", "invalid.jwt.token");

        // Act
        var response = await authenticatedClient.GetAsync("/api/auth/me");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task Login_WithInactiveUser_ReturnsUnauthorized()
    {
        // Arrange
        var email = "inactive@example.com";
        var password = "TestPassword123!";
        await _factory.SeedUserAsync(email, password, isActive: false);

        var loginRequest = new
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/auth/login", loginRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task Login_WithRememberMe_ReturnsExtendedRefreshTokenExpiry()
    {
        // Arrange
        var email = "test@example.com";
        var password = "TestPassword123!";
        await _factory.SeedUserAsync(email, password);

        var loginRequestWithRememberMe = new
        {
            Email = email,
            Password = password,
            RememberMe = true
        };

        var loginRequestWithoutRememberMe = new
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        var responseWithRememberMe = await _client.PostAsJsonAsync("/api/auth/login", loginRequestWithRememberMe);
        var contentWithRememberMe = await responseWithRememberMe.Content.ReadFromJsonAsync<LoginResponseDto>(_jsonOptions);

        await _factory.ResetDatabaseAsync();
        await _factory.SeedUserAsync(email, password);

        var responseWithoutRememberMe = await _client.PostAsJsonAsync("/api/auth/login", loginRequestWithoutRememberMe);
        var contentWithoutRememberMe = await responseWithoutRememberMe.Content.ReadFromJsonAsync<LoginResponseDto>(_jsonOptions);

        // Assert
        contentWithRememberMe.Should().NotBeNull();
        contentWithoutRememberMe.Should().NotBeNull();

        // With RememberMe, refresh token should expire in 30 days vs 7 days without
        var expiryDifferenceInDays = (contentWithRememberMe!.RefreshTokenExpiresAt - contentWithoutRememberMe!.RefreshTokenExpiresAt).TotalDays;
        expiryDifferenceInDays.Should().BeGreaterThan(20); // Should be approximately 23 days difference
    }

    [Fact]
    public async Task ForgotPassword_WithAnyEmail_ReturnsSuccess()
    {
        // Arrange - Note: This endpoint should always return success to prevent email enumeration
        var forgotPasswordRequest = new
        {
            Email = "anyemail@example.com"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/auth/forgot-password", forgotPasswordRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task Login_UpdatesLastLoginAt()
    {
        // Arrange
        var email = "test@example.com";
        var password = "TestPassword123!";
        await _factory.SeedUserAsync(email, password);

        var loginRequest = new
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/auth/login", loginRequest);
        var content = await response.Content.ReadFromJsonAsync<LoginResponseDto>(_jsonOptions);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        content!.User.LastLoginAt.Should().NotBeNull();
        content.User.LastLoginAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }
}

/// <summary>
/// Test-specific DbContext that doesn't apply relational configurations.
/// </summary>
public class TestDbContext : DbContext, IApplicationDbContext
{
    private readonly ICurrentUserService _currentUserService;

    public TestDbContext(
        DbContextOptions<TestDbContext> options,
        ICurrentUserService currentUserService)
        : base(options)
    {
        _currentUserService = currentUserService;
    }

    public DbSet<User> Users => Set<User>();
    public DbSet<RefreshToken> RefreshTokens => Set<RefreshToken>();
    public DbSet<Client> Clients => Set<Client>();
    public DbSet<SystemSetting> SystemSettings => Set<SystemSetting>();
    public DbSet<UnitOfMeasure> UnitsOfMeasure => Set<UnitOfMeasure>();
    public DbSet<Tender> Tenders => Set<Tender>();
    public DbSet<EvaluationCriteria> EvaluationCriteria => Set<EvaluationCriteria>();
    public DbSet<TenderBidder> TenderBidders => Set<TenderBidder>();
    public DbSet<Bidder> Bidders => Set<Bidder>();
    public DbSet<BidSubmission> BidSubmissions => Set<BidSubmission>();
    public DbSet<Clarification> Clarifications => Set<Clarification>();
    public DbSet<Addendum> Addenda => Set<Addendum>();
    public DbSet<Document> Documents => Set<Document>();
    public DbSet<AddendumAcknowledgment> AddendumAcknowledgments => Set<AddendumAcknowledgment>();
    public DbSet<EmailLog> EmailLogs => Set<EmailLog>();
    public DbSet<ClarificationBulletin> ClarificationBulletins => Set<ClarificationBulletin>();
    public DbSet<BoqSection> BoqSections => Set<BoqSection>();
    public DbSet<BoqItem> BoqItems => Set<BoqItem>();
    public DbSet<UomMaster> UomMasters => Set<UomMaster>();
    public DbSet<BidDocument> BidDocuments => Set<BidDocument>();
    public DbSet<BidderRefreshToken> BidderRefreshTokens => Set<BidderRefreshToken>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();
    public DbSet<BidPricing> BidPricings => Set<BidPricing>();
    public DbSet<VendorPricingSnapshot> VendorPricingSnapshots => Set<VendorPricingSnapshot>();
    public DbSet<VendorItemRate> VendorItemRates => Set<VendorItemRate>();
    public DbSet<EvaluationPanel> EvaluationPanels => Set<EvaluationPanel>();
    public DbSet<TechnicalScore> TechnicalScores => Set<TechnicalScore>();
    public DbSet<EvaluationState> EvaluationStates => Set<EvaluationState>();
    public DbSet<CommercialScore> CommercialScores => Set<CommercialScore>();
    public DbSet<CombinedScorecard> CombinedScorecards => Set<CombinedScorecard>();
    public DbSet<BidException> BidExceptions => Set<BidException>();
    public DbSet<ApprovalWorkflow> ApprovalWorkflows => Set<ApprovalWorkflow>();
    public DbSet<ApprovalLevel> ApprovalLevels => Set<ApprovalLevel>();
    public DbSet<NotificationPreference> NotificationPreferences => Set<NotificationPreference>();

    public override async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        foreach (var entry in ChangeTracker.Entries<IAuditableEntity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedBy = _currentUserService.UserId;
                    entry.Entity.CreatedAt = DateTime.UtcNow;
                    break;

                case EntityState.Modified:
                    entry.Entity.LastModifiedBy = _currentUserService.UserId;
                    entry.Entity.LastModifiedAt = DateTime.UtcNow;
                    break;
            }
        }

        foreach (var entry in ChangeTracker.Entries<BaseEntity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    if (entry.Entity.Id == Guid.Empty)
                    {
                        entry.Entity.Id = Guid.NewGuid();
                    }
                    entry.Entity.CreatedAt = DateTime.UtcNow;
                    break;

                case EntityState.Modified:
                    entry.Entity.UpdatedAt = DateTime.UtcNow;
                    break;
            }
        }

        return await base.SaveChangesAsync(cancellationToken);
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Only configure the minimal entities needed for auth tests
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.Email).IsUnique();
        });

        modelBuilder.Entity<RefreshToken>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasOne(e => e.User)
                .WithMany(u => u.RefreshTokens)
                .HasForeignKey(e => e.UserId);
        });

        modelBuilder.Entity<Client>(entity =>
        {
            entity.HasKey(e => e.Id);
        });

        modelBuilder.Entity<SystemSetting>(entity =>
        {
            entity.HasKey(e => e.Id);
        });

        modelBuilder.Entity<UnitOfMeasure>(entity =>
        {
            entity.HasKey(e => e.Id);
        });
    }
}

/// <summary>
/// Custom WebApplicationFactory for integration testing.
/// </summary>
public class BayanWebApplicationFactory : WebApplicationFactory<Program>
{
    private readonly string _databaseName = Guid.NewGuid().ToString();

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        // Set environment to Testing to avoid database migrations and seeding
        builder.UseEnvironment("Testing");

        // Configure app configuration to provide test values
        builder.ConfigureAppConfiguration((context, config) =>
        {
            // Clear existing configuration and add test configuration
            config.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["ConnectionStrings:DefaultConnection"] = "Host=localhost;Database=test;Username=test;Password=test",
                ["JwtSettings:SecretKey"] = "this-is-a-very-long-secret-key-for-testing-purposes-at-least-32-characters",
                ["JwtSettings:Issuer"] = "BayanTestIssuer",
                ["JwtSettings:Audience"] = "BayanTestAudience",
                ["JwtSettings:AccessTokenExpirationMinutes"] = "60",
                ["JwtSettings:RefreshTokenExpirationDays"] = "7",
                ["AllowedOrigins:0"] = "http://localhost:3000",
                ["FrontendUrl"] = "http://localhost:3000"
            });
        });

        builder.ConfigureServices(services =>
        {
            // Remove existing DbContext registrations
            services.RemoveAll(typeof(DbContextOptions<Bayan.Infrastructure.Persistence.ApplicationDbContext>));
            services.RemoveAll(typeof(Bayan.Infrastructure.Persistence.ApplicationDbContext));

            // Add test DbContext with in-memory database
            services.AddDbContext<TestDbContext>((sp, options) =>
            {
                options.UseInMemoryDatabase(_databaseName);
            });

            // Re-register IApplicationDbContext to use TestDbContext
            services.RemoveAll(typeof(IApplicationDbContext));
            services.AddScoped<IApplicationDbContext>(sp =>
                sp.GetRequiredService<TestDbContext>());

            // Replace ICurrentUserService with a mock for testing
            services.RemoveAll(typeof(ICurrentUserService));
            services.AddScoped<ICurrentUserService>(_ => CreateMockCurrentUserService());

            // Replace email service with a mock
            services.RemoveAll(typeof(IEmailService));
            services.AddScoped<IEmailService>(_ =>
            {
                var mock = new Mock<IEmailService>();
                mock.Setup(x => x.SendUserInvitationEmailAsync(
                        It.IsAny<string>(),
                        It.IsAny<string>(),
                        It.IsAny<string>(),
                        It.IsAny<CancellationToken>()))
                    .Returns(Task.CompletedTask);
                mock.Setup(x => x.SendPasswordResetEmailAsync(
                        It.IsAny<string>(),
                        It.IsAny<string>(),
                        It.IsAny<string>(),
                        It.IsAny<string>(),
                        It.IsAny<CancellationToken>()))
                    .Returns(Task.CompletedTask);
                return mock.Object;
            });

            // Remove health checks that require database connection
            services.RemoveAll(typeof(Microsoft.Extensions.Diagnostics.HealthChecks.IHealthCheck));
        });
    }

    private static ICurrentUserService CreateMockCurrentUserService()
    {
        var mock = new Mock<ICurrentUserService>();
        mock.Setup(x => x.UserId).Returns((Guid?)null);
        mock.Setup(x => x.IsAuthenticated).Returns(false);
        mock.Setup(x => x.Email).Returns((string?)null);
        mock.Setup(x => x.Role).Returns((string?)null);
        return mock.Object;
    }

    /// <summary>
    /// Seeds a test user into the database.
    /// </summary>
    public async Task SeedUserAsync(string email, string password, bool isActive = true)
    {
        using var scope = Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<TestDbContext>();
        var passwordHasher = scope.ServiceProvider.GetRequiredService<IPasswordHasher>();

        var user = new User
        {
            Id = Guid.NewGuid(),
            Email = email.ToLower(),
            PasswordHash = passwordHasher.HashPassword(password),
            FirstName = "Test",
            LastName = "User",
            Role = UserRole.Admin,
            IsActive = isActive,
            EmailVerified = true,
            FailedLoginAttempts = 0,
            CreatedAt = DateTime.UtcNow
        };

        context.Users.Add(user);
        await context.SaveChangesAsync();
    }

    /// <summary>
    /// Resets the database for a clean test environment.
    /// Clears all entities in dependency order (children before parents).
    /// </summary>
    public async Task ResetDatabaseAsync()
    {
        using var scope = Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<TestDbContext>();

        // Remove child entities first to respect foreign key ordering
        context.BidDocuments.RemoveRange(context.BidDocuments);
        context.BidSubmissions.RemoveRange(context.BidSubmissions);
        context.BoqItems.RemoveRange(context.BoqItems);
        context.BoqSections.RemoveRange(context.BoqSections);
        context.TenderBidders.RemoveRange(context.TenderBidders);
        context.Bidders.RemoveRange(context.Bidders);
        context.Tenders.RemoveRange(context.Tenders);
        context.Clients.RemoveRange(context.Clients);
        context.RefreshTokens.RemoveRange(context.RefreshTokens);
        context.Users.RemoveRange(context.Users);

        await context.SaveChangesAsync();
    }
}
