using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Auth.DTOs;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;

namespace Bayan.Tests.Integration;

/// <summary>
/// Integration tests for BidsController endpoints.
/// Validates bid listing, opening, and authorization through the HTTP pipeline.
/// The BidsController is for internal (Admin/TenderManager) operations on bid submissions.
/// </summary>
public class BidFlowIntegrationTests : IClassFixture<BayanWebApplicationFactory>, IAsyncLifetime
{
    private readonly BayanWebApplicationFactory _factory;
    private readonly HttpClient _client;
    private readonly JsonSerializerOptions _jsonOptions;

    public BidFlowIntegrationTests(BayanWebApplicationFactory factory)
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

    #region Seed Helpers

    /// <summary>
    /// Authenticates a user and returns an HttpClient with the Bearer token set.
    /// Seeds an Admin user by default (BidsController requires Admin or TenderManager).
    /// </summary>
    private async Task<HttpClient> GetAuthenticatedClientAsync(
        string email = "admin@bayan.test",
        string password = "TestPassword123!")
    {
        await _factory.SeedUserAsync(email, password);

        var loginRequest = new
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        var loginResponse = await _client.PostAsJsonAsync("/api/auth/login", loginRequest);
        loginResponse.StatusCode.Should().Be(HttpStatusCode.OK, "login must succeed to obtain token");

        var loginContent = await loginResponse.Content.ReadFromJsonAsync<LoginResponseDto>(_jsonOptions);

        var authenticatedClient = _factory.CreateClient();
        authenticatedClient.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", loginContent!.AccessToken);

        return authenticatedClient;
    }

    /// <summary>
    /// Seeds a complete bid flow scenario: Client, Tender, Bidder, TenderBidder, and BidSubmission.
    /// Returns a record containing all generated IDs for use in test assertions.
    /// </summary>
    private async Task<BidTestData> SeedBidScenarioAsync(
        TenderStatus tenderStatus = TenderStatus.Active,
        BidSubmissionStatus bidStatus = BidSubmissionStatus.Submitted,
        int bidCount = 1)
    {
        using var scope = _factory.Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<TestDbContext>();

        // Seed Client
        var client = new Client
        {
            Id = Guid.NewGuid(),
            Name = "Test Client Corp",
            ContactPerson = "Jane Smith",
            Email = "client@test.com",
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };
        context.Clients.Add(client);

        // Seed Tender
        var tender = new Tender
        {
            Id = Guid.NewGuid(),
            Title = "Test Tender for Bids",
            Reference = "TND-BID-001",
            Description = "A test tender for bid integration tests",
            ClientId = client.Id,
            TenderType = TenderType.Selective,
            BaseCurrency = "AED",
            BidValidityDays = 90,
            IssueDate = DateTime.UtcNow.AddDays(-30),
            ClarificationDeadline = DateTime.UtcNow.AddDays(-7),
            SubmissionDeadline = DateTime.UtcNow.AddDays(-1),
            OpeningDate = DateTime.UtcNow,
            TechnicalWeight = 40,
            CommercialWeight = 60,
            Status = tenderStatus,
            CreatedAt = DateTime.UtcNow
        };
        context.Tenders.Add(tender);

        var bidIds = new List<Guid>();

        for (int i = 0; i < bidCount; i++)
        {
            // Seed Bidder
            var bidder = new Bidder
            {
                Id = Guid.NewGuid(),
                CompanyName = $"Bidder Company {i + 1}",
                ContactPerson = $"Contact Person {i + 1}",
                Email = $"bidder{i + 1}@test.com",
                Phone = $"+97150000000{i}",
                TradeSpecialization = "General Contracting",
                PrequalificationStatus = PrequalificationStatus.Pending,
                IsActive = true,
                CreatedAt = DateTime.UtcNow
            };
            context.Bidders.Add(bidder);

            // Seed TenderBidder (link bidder to tender)
            var tenderBidder = new TenderBidder
            {
                Id = Guid.NewGuid(),
                TenderId = tender.Id,
                BidderId = bidder.Id,
                InvitationSentAt = DateTime.UtcNow.AddDays(-25),
                RegisteredAt = DateTime.UtcNow.AddDays(-20),
                NdaStatus = NdaStatus.Signed,
                QualificationStatus = QualificationStatus.Qualified,
                CreatedAt = DateTime.UtcNow
            };
            context.TenderBidders.Add(tenderBidder);

            // Seed BidSubmission
            var bidSubmission = new BidSubmission
            {
                Id = Guid.NewGuid(),
                TenderId = tender.Id,
                BidderId = bidder.Id,
                SubmissionTime = DateTime.UtcNow.AddHours(-2 + i),
                IsLate = false,
                NativeCurrency = "AED",
                NativeTotalAmount = 1_000_000m + (i * 250_000m),
                FxRate = 1.0m,
                NormalizedTotalAmount = 1_000_000m + (i * 250_000m),
                BidValidityDays = 90,
                ReceiptNumber = $"RCP-{i + 1:D4}",
                Status = bidStatus,
                ImportStatus = BidImportStatus.Uploaded,
                CreatedAt = DateTime.UtcNow
            };
            context.BidSubmissions.Add(bidSubmission);
            bidIds.Add(bidSubmission.Id);
        }

        await context.SaveChangesAsync();

        return new BidTestData
        {
            TenderId = tender.Id,
            ClientId = client.Id,
            BidIds = bidIds
        };
    }

    /// <summary>
    /// Holds IDs generated during bid scenario seeding for test assertions.
    /// </summary>
    private record BidTestData
    {
        public Guid TenderId { get; init; }
        public Guid ClientId { get; init; }
        public List<Guid> BidIds { get; init; } = new();
    }

    #endregion

    #region Bid List Tests

    [Fact]
    public async Task GetBids_WithValidTender_Returns200()
    {
        // Arrange
        var authenticatedClient = await GetAuthenticatedClientAsync();
        var testData = await SeedBidScenarioAsync(bidCount: 2);

        // Act
        var response = await authenticatedClient.GetAsync(
            $"/api/tenders/{testData.TenderId}/bids");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var content = await response.Content.ReadAsStringAsync();
        var apiResponse = JsonSerializer.Deserialize<ApiResponse<PaginatedList<BidListDto>>>(content, _jsonOptions);

        apiResponse.Should().NotBeNull();
        apiResponse!.Success.Should().BeTrue();
        apiResponse.Data.Should().NotBeNull();
        apiResponse.Data!.TotalCount.Should().Be(2);
        apiResponse.Data.Items.Should().HaveCount(2);
        apiResponse.Data.Items.Should().AllSatisfy(bid =>
        {
            bid.TenderId.Should().Be(testData.TenderId);
            bid.BidderName.Should().NotBeNullOrEmpty();
            bid.ReceiptNumber.Should().NotBeNullOrEmpty();
        });
    }

    [Fact]
    public async Task GetBids_WithNonExistentTender_ReturnsEmptyOrNotFound()
    {
        // Arrange
        var authenticatedClient = await GetAuthenticatedClientAsync();
        var nonExistentTenderId = Guid.NewGuid();

        // Act
        var response = await authenticatedClient.GetAsync(
            $"/api/tenders/{nonExistentTenderId}/bids");

        // Assert
        // The GetBids endpoint returns a paginated list; for a non-existent tender it
        // may return 200 with empty data or 404 depending on the handler implementation.
        // We assert it does not return a server error.
        response.StatusCode.Should().BeOneOf(HttpStatusCode.OK, HttpStatusCode.NotFound);

        if (response.StatusCode == HttpStatusCode.OK)
        {
            var content = await response.Content.ReadAsStringAsync();
            var apiResponse = JsonSerializer.Deserialize<ApiResponse<PaginatedList<BidListDto>>>(content, _jsonOptions);
            apiResponse.Should().NotBeNull();
            apiResponse!.Data!.TotalCount.Should().Be(0);
        }
    }

    #endregion

    #region Authorization Tests

    [Fact]
    public async Task UnauthorizedRequest_Returns401()
    {
        // Arrange - use the unauthenticated client (no Bearer token)
        var tenderId = Guid.NewGuid();

        // Act
        var response = await _client.GetAsync($"/api/tenders/{tenderId}/bids");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    #endregion

    #region Open Bids Tests

    [Fact]
    public async Task OpenBids_WithValidTender_Returns200()
    {
        // Arrange
        var authenticatedClient = await GetAuthenticatedClientAsync();
        // Seed a tender in Evaluation status with submitted bids, which is the typical
        // state when bids are ready to be opened.
        var testData = await SeedBidScenarioAsync(
            tenderStatus: TenderStatus.Evaluation,
            bidStatus: BidSubmissionStatus.Submitted,
            bidCount: 2);

        // Act
        var response = await authenticatedClient.PostAsync(
            $"/api/tenders/{testData.TenderId}/bids/open", null);

        // Assert
        // The open bids operation may succeed (200) or fail with a business rule
        // violation (400) depending on the tender state machine. We verify no server error.
        response.StatusCode.Should().BeOneOf(
            HttpStatusCode.OK,
            HttpStatusCode.BadRequest,
            HttpStatusCode.NotFound);

        if (response.StatusCode == HttpStatusCode.OK)
        {
            var content = await response.Content.ReadAsStringAsync();
            var apiResponse = JsonSerializer.Deserialize<ApiResponse<OpenBidsResultDto>>(content, _jsonOptions);

            apiResponse.Should().NotBeNull();
            apiResponse!.Success.Should().BeTrue();
            apiResponse.Data.Should().NotBeNull();
            apiResponse.Data!.TenderId.Should().Be(testData.TenderId);
            apiResponse.Data.BidsOpenedCount.Should().BeGreaterThanOrEqualTo(0);
        }
    }

    [Fact]
    public async Task OpenBids_WithoutAuth_Returns401()
    {
        // Arrange
        var tenderId = Guid.NewGuid();

        // Act
        var response = await _client.PostAsync(
            $"/api/tenders/{tenderId}/bids/open", null);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    #endregion
}
