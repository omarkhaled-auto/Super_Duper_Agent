using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.Commands.CreateTender;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Application.Features.Tenders.Queries.GetNextTenderReference;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using MediatR;
using Microsoft.EntityFrameworkCore;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Tenders;

/// <summary>
/// Unit tests for CreateTenderCommandHandler.
/// </summary>
public class CreateTenderCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly Mock<IMediator> _mediatorMock;
    private readonly Mock<ICurrentUserService> _currentUserServiceMock;
    private readonly CreateTenderCommandHandler _handler;

    private readonly Guid _currentUserId = Guid.NewGuid();
    private readonly Guid _validClientId = Guid.NewGuid();
    private readonly string _generatedReference = "TNR-2026-0001";

    public CreateTenderCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _mapperMock = new Mock<IMapper>();
        _mediatorMock = new Mock<IMediator>();
        _currentUserServiceMock = new Mock<ICurrentUserService>();

        _currentUserServiceMock.Setup(x => x.UserId).Returns(_currentUserId);
        _currentUserServiceMock.Setup(x => x.Email).Returns("admin@bayan.test");

        _mediatorMock
            .Setup(x => x.Send(It.IsAny<GetNextTenderReferenceQuery>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(_generatedReference);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        _handler = new CreateTenderCommandHandler(
            _contextMock.Object,
            _mapperMock.Object,
            _mediatorMock.Object,
            _currentUserServiceMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidData_CreatesTenderSuccessfully()
    {
        // Arrange
        var command = CreateValidCommand();
        var client = CreateTestClient(_validClientId);
        SetupTendersDbSet(new List<Tender>());
        SetupClientsDbSet(new List<Client> { client });

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Title.Should().Be(command.Title);
        result.ClientId.Should().Be(_validClientId);
        result.ClientName.Should().Be(client.Name);
        _contextMock.Verify(x => x.Tenders.Add(It.IsAny<Tender>()), Times.Once);
    }

    [Fact]
    public async Task Handle_WithValidData_SetsStatusToDraft()
    {
        // Arrange
        var command = CreateValidCommand();
        Tender? capturedTender = null;

        SetupTendersDbSetWithCapture(t => capturedTender = t);
        SetupClientsDbSet(new List<Client> { CreateTestClient(_validClientId) });

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        capturedTender.Should().NotBeNull();
        capturedTender!.Status.Should().Be(TenderStatus.Draft);
    }

    [Fact]
    public async Task Handle_WithValidData_SetsCreatedByToCurrentUser()
    {
        // Arrange
        var command = CreateValidCommand();
        Tender? capturedTender = null;

        SetupTendersDbSetWithCapture(t => capturedTender = t);
        SetupClientsDbSet(new List<Client> { CreateTestClient(_validClientId) });

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        capturedTender.Should().NotBeNull();
        capturedTender!.CreatedBy.Should().Be(_currentUserId);
    }

    [Fact]
    public async Task Handle_WithValidData_GeneratesReferenceNumber()
    {
        // Arrange
        var command = CreateValidCommand();
        Tender? capturedTender = null;

        SetupTendersDbSetWithCapture(t => capturedTender = t);
        SetupClientsDbSet(new List<Client> { CreateTestClient(_validClientId) });

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        capturedTender.Should().NotBeNull();
        capturedTender!.Reference.Should().Be(_generatedReference);
        result.Reference.Should().Be(_generatedReference);
        _mediatorMock.Verify(
            x => x.Send(It.IsAny<GetNextTenderReferenceQuery>(), It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Handle_WithInvalidClient_ReturnsEmptyClientName()
    {
        // Arrange
        var command = CreateValidCommand();

        SetupTendersDbSet(new List<Tender>());
        // No matching client in the database
        SetupClientsDbSet(new List<Client>());

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.ClientName.Should().Be(string.Empty);
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var command = CreateValidCommand();

        SetupTendersDbSet(new List<Tender>());
        SetupClientsDbSet(new List<Client> { CreateTestClient(_validClientId) });

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _contextMock.Verify(
            x => x.SaveChangesAsync(It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Handle_WithValidData_SetsDatesCorrectly()
    {
        // Arrange
        var issueDate = DateTime.UtcNow;
        var clarificationDeadline = issueDate.AddDays(7);
        var submissionDeadline = clarificationDeadline.AddDays(14);
        var openingDate = submissionDeadline.AddDays(1);

        var command = CreateValidCommand();
        command.IssueDate = issueDate;
        command.ClarificationDeadline = clarificationDeadline;
        command.SubmissionDeadline = submissionDeadline;
        command.OpeningDate = openingDate;

        Tender? capturedTender = null;
        SetupTendersDbSetWithCapture(t => capturedTender = t);
        SetupClientsDbSet(new List<Client> { CreateTestClient(_validClientId) });

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        capturedTender.Should().NotBeNull();
        capturedTender!.IssueDate.Should().Be(issueDate);
        capturedTender.ClarificationDeadline.Should().Be(clarificationDeadline);
        capturedTender.SubmissionDeadline.Should().Be(submissionDeadline);
        capturedTender.OpeningDate.Should().Be(openingDate);
        capturedTender.CreatedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_WithValidData_SetsWeightsCorrectly()
    {
        // Arrange
        var command = CreateValidCommand();
        command.TechnicalWeight = 30;
        command.CommercialWeight = 70;

        Tender? capturedTender = null;
        SetupTendersDbSetWithCapture(t => capturedTender = t);
        SetupClientsDbSet(new List<Client> { CreateTestClient(_validClientId) });

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        capturedTender.Should().NotBeNull();
        capturedTender!.TechnicalWeight.Should().Be(30);
        capturedTender.CommercialWeight.Should().Be(70);
        (capturedTender.TechnicalWeight + capturedTender.CommercialWeight).Should().Be(100);
    }

    [Fact]
    public async Task Handle_WithValidData_ReturnsTenderDto()
    {
        // Arrange
        var command = CreateValidCommand();
        var client = CreateTestClient(_validClientId);

        SetupTendersDbSet(new List<Tender>());
        SetupClientsDbSet(new List<Client> { client });

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Should().BeOfType<TenderDto>();
        result.Id.Should().NotBe(Guid.Empty);
        result.Title.Should().Be(command.Title);
        result.Reference.Should().Be(_generatedReference);
        result.ClientId.Should().Be(_validClientId);
        result.ClientName.Should().Be(client.Name);
        result.TenderType.Should().Be(command.TenderType);
        result.BaseCurrency.Should().Be(command.BaseCurrency);
        result.Status.Should().Be(TenderStatus.Draft);
        result.SubmissionDeadline.Should().Be(command.SubmissionDeadline);
        result.BidderCount.Should().Be(0);
        result.BidCount.Should().Be(0);
    }

    #region Helper Methods

    private CreateTenderCommand CreateValidCommand()
    {
        var issueDate = DateTime.UtcNow;
        return new CreateTenderCommand
        {
            Title = "Test Tender for Building Construction",
            Description = "A comprehensive tender for building construction services.",
            ClientId = _validClientId,
            TenderType = TenderType.Open,
            BaseCurrency = "AED",
            BidValidityDays = 90,
            IssueDate = issueDate,
            ClarificationDeadline = issueDate.AddDays(7),
            SubmissionDeadline = issueDate.AddDays(21),
            OpeningDate = issueDate.AddDays(22),
            TechnicalWeight = 40,
            CommercialWeight = 60,
            EvaluationCriteria = new List<CreateEvaluationCriterionDto>()
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
        mockDbSet.Setup(x => x.Add(It.IsAny<Tender>()))
            .Callback<Tender>(tender => tenders.Add(tender));
        _contextMock.Setup(x => x.Tenders).Returns(mockDbSet.Object);
    }

    private void SetupTendersDbSetWithCapture(Action<Tender> captureAction)
    {
        var tenders = new List<Tender>();
        var mockDbSet = tenders.AsQueryable().BuildMockDbSet();
        mockDbSet.Setup(x => x.Add(It.IsAny<Tender>()))
            .Callback<Tender>(tender =>
            {
                tenders.Add(tender);
                captureAction(tender);
            });
        _contextMock.Setup(x => x.Tenders).Returns(mockDbSet.Object);
    }

    private void SetupClientsDbSet(List<Client> clients)
    {
        var mockDbSet = clients.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Clients).Returns(mockDbSet.Object);
    }

    #endregion
}
