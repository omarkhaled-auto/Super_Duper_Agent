using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.Commands.UpdateTender;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Tenders;

/// <summary>
/// Unit tests for UpdateTenderCommandHandler.
/// </summary>
public class UpdateTenderCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly Mock<ICurrentUserService> _currentUserServiceMock;
    private readonly UpdateTenderCommandHandler _handler;

    private readonly Guid _currentUserId = Guid.NewGuid();
    private readonly Guid _validClientId = Guid.NewGuid();
    private readonly Guid _existingTenderId = Guid.NewGuid();

    public UpdateTenderCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _mapperMock = new Mock<IMapper>();
        _currentUserServiceMock = new Mock<ICurrentUserService>();

        _currentUserServiceMock.Setup(x => x.UserId).Returns(_currentUserId);
        _currentUserServiceMock.Setup(x => x.Email).Returns("admin@bayan.test");

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        _handler = new UpdateTenderCommandHandler(
            _contextMock.Object,
            _mapperMock.Object,
            _currentUserServiceMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidData_UpdatesTenderSuccessfully()
    {
        // Arrange
        var existingTender = CreateExistingTender();
        var client = CreateTestClient(_validClientId);
        existingTender.Client = client;

        var command = CreateValidUpdateCommand();

        SetupTendersDbSet(new List<Tender> { existingTender });
        SetupClientsDbSet(new List<Client> { client });
        SetupEvaluationCriteriaDbSet(new List<EvaluationCriteria>());

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result!.Title.Should().Be(command.Title);
        result.ClientId.Should().Be(command.ClientId);
    }

    [Fact]
    public async Task Handle_WithNonExistentTender_ReturnsNull()
    {
        // Arrange
        var command = CreateValidUpdateCommand();
        command.Id = Guid.NewGuid(); // Non-existent ID

        SetupTendersDbSet(new List<Tender>());

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public async Task Handle_WithPublishedTender_StillUpdates()
    {
        // Arrange
        // NOTE: The handler itself does NOT check status; validation is done by the validator.
        // The handler will update regardless of status. This test documents actual behavior.
        var existingTender = CreateExistingTender();
        existingTender.Status = TenderStatus.Active;
        var client = CreateTestClient(_validClientId);
        existingTender.Client = client;

        var command = CreateValidUpdateCommand();

        SetupTendersDbSet(new List<Tender> { existingTender });
        SetupClientsDbSet(new List<Client> { client });
        SetupEvaluationCriteriaDbSet(new List<EvaluationCriteria>());

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        // Handler does not guard status; the validator (UpdateTenderCommandValidator)
        // enforces the Draft-only rule. Handler proceeds with the update.
        result.Should().NotBeNull();
        result!.Title.Should().Be(command.Title);
    }

    [Fact]
    public async Task Handle_UpdatesTitle()
    {
        // Arrange
        var existingTender = CreateExistingTender();
        existingTender.Title = "Original Title";
        var client = CreateTestClient(_validClientId);
        existingTender.Client = client;

        var command = CreateValidUpdateCommand();
        command.Title = "Updated Tender Title for Road Construction";

        SetupTendersDbSet(new List<Tender> { existingTender });
        SetupClientsDbSet(new List<Client> { client });
        SetupEvaluationCriteriaDbSet(new List<EvaluationCriteria>());

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result!.Title.Should().Be("Updated Tender Title for Road Construction");
        existingTender.Title.Should().Be("Updated Tender Title for Road Construction");
    }

    [Fact]
    public async Task Handle_UpdatesDeadlines()
    {
        // Arrange
        var existingTender = CreateExistingTender();
        var client = CreateTestClient(_validClientId);
        existingTender.Client = client;

        var newIssueDate = DateTime.UtcNow.AddDays(1);
        var newClarificationDeadline = newIssueDate.AddDays(10);
        var newSubmissionDeadline = newClarificationDeadline.AddDays(20);
        var newOpeningDate = newSubmissionDeadline.AddDays(2);

        var command = CreateValidUpdateCommand();
        command.IssueDate = newIssueDate;
        command.ClarificationDeadline = newClarificationDeadline;
        command.SubmissionDeadline = newSubmissionDeadline;
        command.OpeningDate = newOpeningDate;

        SetupTendersDbSet(new List<Tender> { existingTender });
        SetupClientsDbSet(new List<Client> { client });
        SetupEvaluationCriteriaDbSet(new List<EvaluationCriteria>());

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        existingTender.IssueDate.Should().Be(newIssueDate);
        existingTender.ClarificationDeadline.Should().Be(newClarificationDeadline);
        existingTender.SubmissionDeadline.Should().Be(newSubmissionDeadline);
        existingTender.OpeningDate.Should().Be(newOpeningDate);
        existingTender.LastModifiedBy.Should().Be(_currentUserId);
        existingTender.LastModifiedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_UpdatesWeights()
    {
        // Arrange
        var existingTender = CreateExistingTender();
        existingTender.TechnicalWeight = 40;
        existingTender.CommercialWeight = 60;
        var client = CreateTestClient(_validClientId);
        existingTender.Client = client;

        var command = CreateValidUpdateCommand();
        command.TechnicalWeight = 70;
        command.CommercialWeight = 30;

        SetupTendersDbSet(new List<Tender> { existingTender });
        SetupClientsDbSet(new List<Client> { client });
        SetupEvaluationCriteriaDbSet(new List<EvaluationCriteria>());

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        existingTender.TechnicalWeight.Should().Be(70);
        existingTender.CommercialWeight.Should().Be(30);
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var existingTender = CreateExistingTender();
        var client = CreateTestClient(_validClientId);
        existingTender.Client = client;

        var command = CreateValidUpdateCommand();

        SetupTendersDbSet(new List<Tender> { existingTender });
        SetupClientsDbSet(new List<Client> { client });
        SetupEvaluationCriteriaDbSet(new List<EvaluationCriteria>());

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _contextMock.Verify(
            x => x.SaveChangesAsync(It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Handle_ReturnsUpdatedTenderDto()
    {
        // Arrange
        var existingTender = CreateExistingTender();
        var client = CreateTestClient(_validClientId);
        existingTender.Client = client;

        var command = CreateValidUpdateCommand();
        command.Title = "Final Updated Title";
        command.BaseCurrency = "USD";

        SetupTendersDbSet(new List<Tender> { existingTender });
        SetupClientsDbSet(new List<Client> { client });
        SetupEvaluationCriteriaDbSet(new List<EvaluationCriteria>());

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Should().BeOfType<TenderDto>();
        result!.Id.Should().Be(_existingTenderId);
        result.Title.Should().Be("Final Updated Title");
        result.BaseCurrency.Should().Be("USD");
        result.Reference.Should().Be(existingTender.Reference);
        result.ClientId.Should().Be(_validClientId);
        result.ClientName.Should().Be(client.Name);
        result.Status.Should().Be(TenderStatus.Draft);
    }

    #region Helper Methods

    private Tender CreateExistingTender()
    {
        return new Tender
        {
            Id = _existingTenderId,
            Title = "Original Tender Title",
            Reference = "TNR-2026-0001",
            Description = "Original description",
            ClientId = _validClientId,
            TenderType = TenderType.Open,
            BaseCurrency = "AED",
            BidValidityDays = 90,
            IssueDate = DateTime.UtcNow.AddDays(-10),
            ClarificationDeadline = DateTime.UtcNow.AddDays(-3),
            SubmissionDeadline = DateTime.UtcNow.AddDays(14),
            OpeningDate = DateTime.UtcNow.AddDays(15),
            TechnicalWeight = 40,
            CommercialWeight = 60,
            Status = TenderStatus.Draft,
            CreatedBy = _currentUserId,
            CreatedAt = DateTime.UtcNow.AddDays(-10),
            EvaluationCriteria = new List<EvaluationCriteria>(),
            TenderBidders = new List<TenderBidder>()
        };
    }

    private UpdateTenderCommand CreateValidUpdateCommand()
    {
        var issueDate = DateTime.UtcNow;
        return new UpdateTenderCommand
        {
            Id = _existingTenderId,
            Title = "Updated Tender Title",
            Description = "Updated description for tender.",
            ClientId = _validClientId,
            TenderType = TenderType.Selective,
            BaseCurrency = "AED",
            BidValidityDays = 120,
            IssueDate = issueDate,
            ClarificationDeadline = issueDate.AddDays(7),
            SubmissionDeadline = issueDate.AddDays(21),
            OpeningDate = issueDate.AddDays(22),
            TechnicalWeight = 50,
            CommercialWeight = 50,
            EvaluationCriteria = new List<UpdateEvaluationCriterionDto>()
        };
    }

    private static Client CreateTestClient(Guid clientId)
    {
        return new Client
        {
            Id = clientId,
            Name = "ADNOC",
            ContactPerson = "John Doe",
            Email = "contact@adnoc.ae",
            Phone = "+971-2-1234567",
            IsActive = true,
            CreatedAt = DateTime.UtcNow.AddMonths(-6)
        };
    }

    private void SetupTendersDbSet(List<Tender> tenders)
    {
        var mockDbSet = tenders.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Tenders).Returns(mockDbSet.Object);
    }

    private void SetupClientsDbSet(List<Client> clients)
    {
        var mockDbSet = clients.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Clients).Returns(mockDbSet.Object);
    }

    private void SetupEvaluationCriteriaDbSet(List<EvaluationCriteria> criteria)
    {
        var mockDbSet = criteria.AsQueryable().BuildMockDbSet();
        mockDbSet.Setup(x => x.Remove(It.IsAny<EvaluationCriteria>()))
            .Callback<EvaluationCriteria>(c => criteria.Remove(c));
        _contextMock.Setup(x => x.EvaluationCriteria).Returns(mockDbSet.Object);
    }

    #endregion
}
