using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.Commands.SubmitClarification;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Application.Features.Clarifications.Queries.GetNextClarificationRef;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using MediatR;
using Microsoft.EntityFrameworkCore;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Clarifications;

/// <summary>
/// Unit tests for SubmitClarificationCommandHandler.
/// Tests clarification submission logic including validation, reference number generation,
/// and status management.
/// </summary>
public class SubmitClarificationCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly Mock<IMediator> _mediatorMock;
    private readonly SubmitClarificationCommandHandler _handler;
    private readonly List<Clarification> _clarificationsStore;

    private readonly Guid _tenderId = Guid.NewGuid();
    private readonly Guid _bidderId = Guid.NewGuid();

    public SubmitClarificationCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _mapperMock = new Mock<IMapper>();
        _mediatorMock = new Mock<IMediator>();
        _clarificationsStore = new List<Clarification>();

        _handler = new SubmitClarificationCommandHandler(
            _contextMock.Object,
            _mapperMock.Object,
            _mediatorMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidData_CreatesClarification()
    {
        // Arrange
        var command = CreateValidCommand();
        SetupValidTender();
        SetupValidTenderBidder();
        SetupClarificationsDbSet();
        SetupReferenceNumberGeneration("CL-001");
        SetupSaveChanges();
        SetupClarificationsReload();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _clarificationsStore.Should().HaveCount(1);
        var created = _clarificationsStore[0];
        created.TenderId.Should().Be(_tenderId);
        created.Subject.Should().Be(command.Subject);
        created.Question.Should().Be(command.Question);
        created.SubmittedByBidderId.Should().Be(_bidderId);
        created.Id.Should().NotBeEmpty();
        created.CreatedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
        created.SubmittedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_WithNonExistentTender_ThrowsNotFoundException()
    {
        // Arrange
        var command = CreateValidCommand();

        // Setup empty tenders list so tender is not found
        SetupTendersDbSet(new List<Tender>());
        SetupValidTenderBidder();
        SetupClarificationsDbSet();

        // Act
        var act = () => _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<NotFoundException>()
            .WithMessage($"*Tender*{_tenderId}*");
    }

    [Fact]
    public async Task Handle_SetsStatusToSubmitted()
    {
        // Arrange
        var command = CreateValidCommand();
        SetupValidTender();
        SetupValidTenderBidder();
        SetupClarificationsDbSet();
        SetupReferenceNumberGeneration("CL-001");
        SetupSaveChanges();
        SetupClarificationsReload();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _clarificationsStore.Should().HaveCount(1);
        _clarificationsStore[0].Status.Should().Be(ClarificationStatus.Submitted);
    }

    [Fact]
    public async Task Handle_GeneratesReferenceNumber()
    {
        // Arrange
        var command = CreateValidCommand();
        var expectedRef = "CL-003";

        SetupValidTender();
        SetupValidTenderBidder();
        SetupClarificationsDbSet();
        SetupReferenceNumberGeneration(expectedRef);
        SetupSaveChanges();
        SetupClarificationsReload();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _clarificationsStore.Should().HaveCount(1);
        _clarificationsStore[0].ReferenceNumber.Should().Be(expectedRef);

        _mediatorMock.Verify(
            x => x.Send(
                It.Is<GetNextClarificationRefQuery>(q => q.TenderId == _tenderId),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Handle_SetsSubmittedByBidderId()
    {
        // Arrange
        var command = CreateValidCommand();
        SetupValidTender();
        SetupValidTenderBidder();
        SetupClarificationsDbSet();
        SetupReferenceNumberGeneration("CL-001");
        SetupSaveChanges();
        SetupClarificationsReload();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _clarificationsStore.Should().HaveCount(1);
        _clarificationsStore[0].SubmittedByBidderId.Should().Be(_bidderId);
    }

    [Fact]
    public async Task Handle_WithAnonymousFlag_SetsIsAnonymous()
    {
        // Arrange
        var command = CreateValidCommand();
        command.IsAnonymous = true;

        SetupValidTender();
        SetupValidTenderBidder();
        SetupClarificationsDbSet();
        SetupReferenceNumberGeneration("CL-001");
        SetupSaveChanges();
        SetupClarificationsReload();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _clarificationsStore.Should().HaveCount(1);
        _clarificationsStore[0].IsAnonymous.Should().BeTrue();
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var command = CreateValidCommand();
        SetupValidTender();
        SetupValidTenderBidder();
        SetupClarificationsDbSet();
        SetupReferenceNumberGeneration("CL-001");
        SetupSaveChanges();
        SetupClarificationsReload();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _contextMock.Verify(
            x => x.SaveChangesAsync(It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Handle_ReturnsClarificationDto()
    {
        // Arrange
        var command = CreateValidCommand();
        var expectedDto = new ClarificationDto
        {
            Id = Guid.NewGuid(),
            TenderId = _tenderId,
            ReferenceNumber = "CL-001",
            Subject = command.Subject,
            Question = command.Question,
            Status = ClarificationStatus.Submitted,
            Priority = ClarificationPriority.Normal,
            SubmittedByBidderId = _bidderId,
            IsAnonymous = false,
            SubmittedAt = DateTime.UtcNow
        };

        SetupValidTender();
        SetupValidTenderBidder();
        SetupClarificationsDbSet();
        SetupReferenceNumberGeneration("CL-001");
        SetupSaveChanges();
        SetupClarificationsReload();

        _mapperMock.Setup(x => x.Map<ClarificationDto>(It.IsAny<Clarification>()))
            .Returns(expectedDto);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.TenderId.Should().Be(_tenderId);
        result.ReferenceNumber.Should().Be("CL-001");
        result.Status.Should().Be(ClarificationStatus.Submitted);
        _mapperMock.Verify(
            x => x.Map<ClarificationDto>(It.IsAny<Clarification>()),
            Times.Once);
    }

    [Fact]
    public async Task Handle_SetsPriorityCorrectly()
    {
        // Arrange
        var command = CreateValidCommand();
        SetupValidTender();
        SetupValidTenderBidder();
        SetupClarificationsDbSet();
        SetupReferenceNumberGeneration("CL-001");
        SetupSaveChanges();
        SetupClarificationsReload();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        // Handler always sets priority to Normal for submitted clarifications
        _clarificationsStore.Should().HaveCount(1);
        _clarificationsStore[0].Priority.Should().Be(ClarificationPriority.Normal);
    }

    [Fact]
    public async Task Handle_WithInactiveTender_ThrowsInvalidOperationException()
    {
        // Arrange
        var command = CreateValidCommand();

        var inactiveTender = CreateTestTender(_tenderId, TenderStatus.Draft);
        SetupTendersDbSet(new List<Tender> { inactiveTender });
        SetupValidTenderBidder();
        SetupClarificationsDbSet();

        // Act
        var act = () => _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*Active*");
    }

    [Fact]
    public async Task Handle_WithExpiredDeadline_ThrowsInvalidOperationException()
    {
        // Arrange
        var command = CreateValidCommand();

        var tender = CreateTestTender(_tenderId, TenderStatus.Active);
        tender.ClarificationDeadline = DateTime.UtcNow.AddDays(-1); // Expired
        SetupTendersDbSet(new List<Tender> { tender });
        SetupValidTenderBidder();
        SetupClarificationsDbSet();

        // Act
        var act = () => _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*deadline*");
    }

    [Fact]
    public async Task Handle_WithBidderNotInvited_ThrowsInvalidOperationException()
    {
        // Arrange
        var command = CreateValidCommand();
        SetupValidTender();

        // Setup empty TenderBidders so bidder is not found
        var emptyTenderBidders = new List<TenderBidder>().AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.TenderBidders).Returns(emptyTenderBidders.Object);

        SetupClarificationsDbSet();

        // Act
        var act = () => _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*not invited*");
    }

    #region Helper Methods

    private SubmitClarificationCommand CreateValidCommand()
    {
        return new SubmitClarificationCommand
        {
            TenderId = _tenderId,
            Subject = "Clarification on concrete specifications",
            Question = "What is the minimum compressive strength required for the foundation concrete?",
            RelatedBoqSection = "Section 3.1",
            RelatedDocumentId = null,
            BidderId = _bidderId,
            AttachmentIds = new List<Guid>(),
            IsAnonymous = false
        };
    }

    private static Tender CreateTestTender(
        Guid tenderId,
        TenderStatus status = TenderStatus.Active)
    {
        return new Tender
        {
            Id = tenderId,
            Title = "Infrastructure Project",
            Reference = "TND-001",
            Status = status,
            ClarificationDeadline = DateTime.UtcNow.AddDays(5),
            SubmissionDeadline = DateTime.UtcNow.AddDays(15),
            OpeningDate = DateTime.UtcNow.AddDays(16),
            IssueDate = DateTime.UtcNow.AddDays(-5),
            TenderType = TenderType.Open,
            BaseCurrency = "AED",
            TechnicalWeight = 40,
            CommercialWeight = 60,
            CreatedAt = DateTime.UtcNow.AddDays(-10)
        };
    }

    private void SetupValidTender()
    {
        var tender = CreateTestTender(_tenderId, TenderStatus.Active);
        SetupTendersDbSet(new List<Tender> { tender });
    }

    private void SetupTendersDbSet(List<Tender> tenders)
    {
        var mockDbSet = tenders.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Tenders).Returns(mockDbSet.Object);
    }

    private void SetupValidTenderBidder()
    {
        var tenderBidder = new TenderBidder
        {
            Id = Guid.NewGuid(),
            TenderId = _tenderId,
            BidderId = _bidderId,
            QualificationStatus = QualificationStatus.Qualified,
            CreatedAt = DateTime.UtcNow
        };

        var mockDbSet = new List<TenderBidder> { tenderBidder }
            .AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.TenderBidders).Returns(mockDbSet.Object);
    }

    private void SetupClarificationsDbSet()
    {
        var mockDbSet = new Mock<DbSet<Clarification>>();

        mockDbSet.Setup(x => x.Add(It.IsAny<Clarification>()))
            .Callback<Clarification>(c => _clarificationsStore.Add(c));

        _contextMock.Setup(x => x.Clarifications).Returns(mockDbSet.Object);
    }

    private void SetupClarificationsReload()
    {
        // After SaveChangesAsync, the handler reloads the clarification with Include.
        // We rebuild the DbSet after save to support the reload query.
        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1)
            .Callback(() =>
            {
                var queryMockDbSet = _clarificationsStore.AsQueryable().BuildMockDbSet();
                _contextMock.Setup(x => x.Clarifications).Returns(queryMockDbSet.Object);
            });
    }

    private void SetupReferenceNumberGeneration(string referenceNumber)
    {
        _mediatorMock.Setup(x => x.Send(
                It.IsAny<GetNextClarificationRefQuery>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(referenceNumber);
    }

    private void SetupSaveChanges()
    {
        // Base setup handled by SetupClarificationsReload callback
    }

    private void SetupMapper()
    {
        _mapperMock.Setup(x => x.Map<ClarificationDto>(It.IsAny<Clarification>()))
            .Returns((Clarification c) => new ClarificationDto
            {
                Id = c.Id,
                TenderId = c.TenderId,
                ReferenceNumber = c.ReferenceNumber,
                Subject = c.Subject,
                Question = c.Question,
                Status = c.Status,
                ClarificationType = c.ClarificationType,
                Priority = c.Priority,
                SubmittedByBidderId = c.SubmittedByBidderId,
                IsAnonymous = c.IsAnonymous,
                SubmittedAt = c.SubmittedAt,
                CreatedAt = c.CreatedAt
            });
    }

    #endregion
}
