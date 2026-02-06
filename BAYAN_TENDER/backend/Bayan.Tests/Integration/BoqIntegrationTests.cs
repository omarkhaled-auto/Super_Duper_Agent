using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Auth.DTOs;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;

namespace Bayan.Tests.Integration;

/// <summary>
/// Integration tests for BoqController endpoints.
/// Validates BOQ section and item CRUD operations through the HTTP pipeline.
/// </summary>
public class BoqIntegrationTests : IClassFixture<BayanWebApplicationFactory>, IAsyncLifetime
{
    private readonly BayanWebApplicationFactory _factory;
    private readonly HttpClient _client;
    private readonly JsonSerializerOptions _jsonOptions;

    public BoqIntegrationTests(BayanWebApplicationFactory factory)
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
    /// Seeds a Client and Tender into the database, returning the Tender ID.
    /// The tender is created in Draft status which allows BOQ modifications.
    /// </summary>
    private async Task<Guid> SeedTenderAsync()
    {
        using var scope = _factory.Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<TestDbContext>();

        var client = new Client
        {
            Id = Guid.NewGuid(),
            Name = "Test Client Corp",
            ContactPerson = "John Doe",
            Email = "client@test.com",
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        context.Clients.Add(client);

        var tender = new Tender
        {
            Id = Guid.NewGuid(),
            Title = "Test Tender for BOQ",
            Reference = "TND-BOQ-001",
            Description = "A test tender for BOQ integration tests",
            ClientId = client.Id,
            TenderType = TenderType.Open,
            BaseCurrency = "AED",
            BidValidityDays = 90,
            IssueDate = DateTime.UtcNow,
            ClarificationDeadline = DateTime.UtcNow.AddDays(14),
            SubmissionDeadline = DateTime.UtcNow.AddDays(30),
            OpeningDate = DateTime.UtcNow.AddDays(31),
            TechnicalWeight = 40,
            CommercialWeight = 60,
            Status = TenderStatus.Draft,
            CreatedAt = DateTime.UtcNow
        };

        context.Tenders.Add(tender);
        await context.SaveChangesAsync();

        return tender.Id;
    }

    /// <summary>
    /// Seeds a BOQ section directly in the database, returning the section ID.
    /// </summary>
    private async Task<Guid> SeedBoqSectionAsync(Guid tenderId, string sectionNumber = "1", string title = "General Requirements")
    {
        using var scope = _factory.Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<TestDbContext>();

        var section = new BoqSection
        {
            Id = Guid.NewGuid(),
            TenderId = tenderId,
            SectionNumber = sectionNumber,
            Title = title,
            SortOrder = 1,
            CreatedAt = DateTime.UtcNow
        };

        context.BoqSections.Add(section);
        await context.SaveChangesAsync();

        return section.Id;
    }

    #endregion

    #region Section Tests

    [Fact]
    public async Task CreateSection_WithValidData_ReturnsCreated()
    {
        // Arrange
        var authenticatedClient = await GetAuthenticatedClientAsync();
        var tenderId = await SeedTenderAsync();

        var createDto = new
        {
            SectionNumber = "1",
            Title = "Structural Works",
            SortOrder = 1,
            ParentSectionId = (Guid?)null
        };

        // Act
        var response = await authenticatedClient.PostAsJsonAsync(
            $"/api/tenders/{tenderId}/boq/sections", createDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);

        var content = await response.Content.ReadAsStringAsync();
        var apiResponse = JsonSerializer.Deserialize<ApiResponse<BoqSectionDto>>(content, _jsonOptions);

        apiResponse.Should().NotBeNull();
        apiResponse!.Success.Should().BeTrue();
        apiResponse.Data.Should().NotBeNull();
        apiResponse.Data!.SectionNumber.Should().Be("1");
        apiResponse.Data.Title.Should().Be("Structural Works");
        apiResponse.Data.SortOrder.Should().Be(1);
        apiResponse.Data.Id.Should().NotBeEmpty();
    }

    [Fact]
    public async Task AddItem_WithValidData_ReturnsCreated()
    {
        // Arrange
        var authenticatedClient = await GetAuthenticatedClientAsync();
        var tenderId = await SeedTenderAsync();
        var sectionId = await SeedBoqSectionAsync(tenderId);

        var createItemDto = new
        {
            SectionId = sectionId,
            ItemNumber = "1.1",
            Description = "Concrete grade C40",
            Quantity = 150.0m,
            Uom = "m3",
            ItemType = (int)BoqItemType.Base,
            Notes = "Including formwork",
            SortOrder = 1
        };

        // Act
        var response = await authenticatedClient.PostAsJsonAsync(
            $"/api/tenders/{tenderId}/boq/items", createItemDto);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);

        var content = await response.Content.ReadAsStringAsync();
        var apiResponse = JsonSerializer.Deserialize<ApiResponse<BoqItemDto>>(content, _jsonOptions);

        apiResponse.Should().NotBeNull();
        apiResponse!.Success.Should().BeTrue();
        apiResponse.Data.Should().NotBeNull();
        apiResponse.Data!.ItemNumber.Should().Be("1.1");
        apiResponse.Data.Description.Should().Be("Concrete grade C40");
        apiResponse.Data.Quantity.Should().Be(150.0m);
        apiResponse.Data.Uom.Should().Be("m3");
        apiResponse.Data.SectionId.Should().Be(sectionId);
        apiResponse.Data.Id.Should().NotBeEmpty();
    }

    [Fact]
    public async Task GetBoqStructure_ReturnsAllSections()
    {
        // Arrange
        var authenticatedClient = await GetAuthenticatedClientAsync();
        var tenderId = await SeedTenderAsync();

        // Seed two sections via the API
        var section1 = new { SectionNumber = "1", Title = "Civil Works", SortOrder = 1, ParentSectionId = (Guid?)null };
        var section2 = new { SectionNumber = "2", Title = "MEP Works", SortOrder = 2, ParentSectionId = (Guid?)null };

        var createResponse1 = await authenticatedClient.PostAsJsonAsync(
            $"/api/tenders/{tenderId}/boq/sections", section1);
        createResponse1.StatusCode.Should().Be(HttpStatusCode.Created);

        var createResponse2 = await authenticatedClient.PostAsJsonAsync(
            $"/api/tenders/{tenderId}/boq/sections", section2);
        createResponse2.StatusCode.Should().Be(HttpStatusCode.Created);

        // Act
        var response = await authenticatedClient.GetAsync($"/api/tenders/{tenderId}/boq");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var content = await response.Content.ReadAsStringAsync();
        var apiResponse = JsonSerializer.Deserialize<ApiResponse<List<BoqTreeNodeDto>>>(content, _jsonOptions);

        apiResponse.Should().NotBeNull();
        apiResponse!.Success.Should().BeTrue();
        apiResponse.Data.Should().NotBeNull();
        apiResponse.Data!.Should().HaveCount(2);
        apiResponse.Data.Should().Contain(s => s.Title == "Civil Works");
        apiResponse.Data.Should().Contain(s => s.Title == "MEP Works");
    }

    [Fact]
    public async Task DeleteSection_WithValidId_ReturnsNoContent()
    {
        // Arrange
        var authenticatedClient = await GetAuthenticatedClientAsync();
        var tenderId = await SeedTenderAsync();

        // Create a section via the API
        var createDto = new { SectionNumber = "1", Title = "To Be Deleted", SortOrder = 1, ParentSectionId = (Guid?)null };
        var createResponse = await authenticatedClient.PostAsJsonAsync(
            $"/api/tenders/{tenderId}/boq/sections", createDto);
        createResponse.StatusCode.Should().Be(HttpStatusCode.Created);

        var createContent = await createResponse.Content.ReadAsStringAsync();
        var createdSection = JsonSerializer.Deserialize<ApiResponse<BoqSectionDto>>(createContent, _jsonOptions);
        var sectionId = createdSection!.Data!.Id;

        // Act
        var response = await authenticatedClient.DeleteAsync(
            $"/api/tenders/{tenderId}/boq/sections/{sectionId}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // Verify the section is gone by querying the BOQ structure
        var getResponse = await authenticatedClient.GetAsync($"/api/tenders/{tenderId}/boq");
        var getContent = await getResponse.Content.ReadAsStringAsync();
        var structure = JsonSerializer.Deserialize<ApiResponse<List<BoqTreeNodeDto>>>(getContent, _jsonOptions);
        structure!.Data.Should().BeEmpty();
    }

    [Fact]
    public async Task UnauthorizedRequest_Returns401()
    {
        // Arrange - use the unauthenticated client (no Bearer token)
        var tenderId = Guid.NewGuid();

        // Act
        var response = await _client.GetAsync($"/api/tenders/{tenderId}/boq");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    #endregion
}
