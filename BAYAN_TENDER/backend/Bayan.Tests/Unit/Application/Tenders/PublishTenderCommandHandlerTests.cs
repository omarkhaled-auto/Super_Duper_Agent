using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.Commands.PublishTender;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Tenders;

/// <summary>
/// Unit tests for PublishTenderCommandHandler.
/// </summary>
public class PublishTenderCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly Mock<ICurrentUserService> _currentUserServiceMock;
    private readonly PublishTenderCommandHandler _handler;
    private readonly Guid _currentUserId = Guid.NewGuid();

    public PublishTenderCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _mapperMock = new Mock<IMapper>();
        _currentUserServiceMock = new Mock<ICurrentUserService>();

        _currentUserServiceMock.Setup(x => x.UserId).Returns(_currentUserId);

        _handler = new PublishTenderCommandHandler(
            _contextMock.Object,
            _mapperMock.Object,
            _currentUserServiceMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidTender_SetsStatusToActive()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var tender = CreateTestTender(tenderId);
        SetupTendersDbSet(new List<Tender> { tender });

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new PublishTenderCommand(tenderId);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        tender.Status.Should().Be(TenderStatus.Active);
    }

    [Fact]
    public async Task Handle_WithValidTender_SetsPublishedAtTimestamp()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var tender = CreateTestTender(tenderId);
        SetupTendersDbSet(new List<Tender> { tender });

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new PublishTenderCommand(tenderId);

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        tender.PublishedAt.Should().NotBeNull();
        tender.PublishedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_WithValidTender_SetsLastModifiedByCurrentUser()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var tender = CreateTestTender(tenderId);
        SetupTendersDbSet(new List<Tender> { tender });

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new PublishTenderCommand(tenderId);

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        tender.LastModifiedBy.Should().Be(_currentUserId);
    }

    [Fact]
    public async Task Handle_WithNonExistentTender_ReturnsNull()
    {
        // Arrange
        SetupTendersDbSet(new List<Tender>());

        var command = new PublishTenderCommand(Guid.NewGuid());

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public async Task Handle_WithValidTender_CallsSaveChangesAsync()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var tender = CreateTestTender(tenderId);
        SetupTendersDbSet(new List<Tender> { tender });

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new PublishTenderCommand(tenderId);

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _contextMock.Verify(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.Once);
    }

    private static Tender CreateTestTender(Guid id)
    {
        var client = new Client
        {
            Id = Guid.NewGuid(),
            Name = "Test Client",
            CreatedAt = DateTime.UtcNow
        };

        return new Tender
        {
            Id = id,
            Title = "Test Tender",
            Reference = "TND-001",
            ClientId = client.Id,
            Client = client,
            TenderType = TenderType.Open,
            BaseCurrency = "AED",
            Status = TenderStatus.Draft,
            IssueDate = DateTime.UtcNow.AddDays(-5),
            ClarificationDeadline = DateTime.UtcNow.AddDays(5),
            SubmissionDeadline = DateTime.UtcNow.AddDays(15),
            OpeningDate = DateTime.UtcNow.AddDays(16),
            TechnicalWeight = 40,
            CommercialWeight = 60,
            CreatedBy = Guid.NewGuid(),
            CreatedAt = DateTime.UtcNow.AddDays(-10),
            TenderBidders = new List<TenderBidder>()
        };
    }

    private void SetupTendersDbSet(List<Tender> tenders)
    {
        var mockDbSet = tenders.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Tenders).Returns(mockDbSet.Object);
    }
}
