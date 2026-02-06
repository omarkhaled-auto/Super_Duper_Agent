using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.Commands.PublishBulletin;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Clarifications;

/// <summary>
/// Unit tests for PublishBulletinCommandHandler.
/// Tests bulletin publishing logic including validation, PDF generation,
/// clarification status updates, and email notification.
/// </summary>
public class PublishBulletinCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IPdfService> _pdfServiceMock;
    private readonly Mock<IFileStorageService> _fileStorageServiceMock;
    private readonly Mock<IEmailService> _emailServiceMock;
    private readonly Mock<ICurrentUserService> _currentUserServiceMock;
    private readonly Mock<ILogger<PublishBulletinCommandHandler>> _loggerMock;
    private readonly PublishBulletinCommandHandler _handler;

    private readonly List<ClarificationBulletin> _bulletinsStore;
    private readonly List<EmailLog> _emailLogsStore;

    private readonly Guid _tenderId = Guid.NewGuid();
    private readonly Guid _currentUserId = Guid.NewGuid();

    public PublishBulletinCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _pdfServiceMock = new Mock<IPdfService>();
        _fileStorageServiceMock = new Mock<IFileStorageService>();
        _emailServiceMock = new Mock<IEmailService>();
        _currentUserServiceMock = new Mock<ICurrentUserService>();
        _loggerMock = new Mock<ILogger<PublishBulletinCommandHandler>>();

        _bulletinsStore = new List<ClarificationBulletin>();
        _emailLogsStore = new List<EmailLog>();

        _currentUserServiceMock.Setup(x => x.UserId).Returns(_currentUserId);

        _handler = new PublishBulletinCommandHandler(
            _contextMock.Object,
            _pdfServiceMock.Object,
            _fileStorageServiceMock.Object,
            _emailServiceMock.Object,
            _currentUserServiceMock.Object,
            _loggerMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidData_CreatesBulletin()
    {
        // Arrange
        var clarificationIds = new List<Guid>();
        var clarifications = CreateAnsweredClarifications(2, out clarificationIds);
        var command = CreateValidCommand(clarificationIds);

        SetupFullValidScenario(clarifications);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        _bulletinsStore.Should().HaveCount(1);
        var bulletin = _bulletinsStore[0];
        bulletin.TenderId.Should().Be(_tenderId);
        bulletin.Introduction.Should().Be(command.Introduction);
        bulletin.ClosingNotes.Should().Be(command.ClosingNotes);
        bulletin.PublishedBy.Should().Be(_currentUserId);
        bulletin.Id.Should().NotBeEmpty();
        bulletin.CreatedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
        bulletin.PublishedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_WithNonExistentTender_ThrowsNotFoundException()
    {
        // Arrange
        var clarificationIds = new List<Guid> { Guid.NewGuid() };
        var command = CreateValidCommand(clarificationIds);

        // Setup empty tenders list
        SetupTendersDbSet(new List<Tender>());

        // Act
        var act = () => _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<NotFoundException>()
            .WithMessage($"*Tender*{_tenderId}*");
    }

    [Fact]
    public async Task Handle_WithNonAnsweredClarifications_ThrowsInvalidOperationException()
    {
        // Arrange
        var clarificationIds = new List<Guid>();
        var clarifications = CreateClarificationsWithMixedStatuses(out clarificationIds);
        var command = CreateValidCommand(clarificationIds);

        SetupValidTender();
        SetupClarificationsDbSetForQuery(clarifications);

        // Act
        var act = () => _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*not in 'Answered' status*");
    }

    [Fact]
    public async Task Handle_UpdatesClarificationStatusToPublished()
    {
        // Arrange
        var clarificationIds = new List<Guid>();
        var clarifications = CreateAnsweredClarifications(3, out clarificationIds);
        var command = CreateValidCommand(clarificationIds);

        SetupFullValidScenario(clarifications);

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        clarifications.Should().OnlyContain(c => c.Status == ClarificationStatus.Published);
        clarifications.Should().OnlyContain(c => c.PublishedInBulletinId != null);
        clarifications.Should().OnlyContain(c => c.PublishedAt != null);
        clarifications.Should().OnlyContain(c => c.UpdatedAt != null);
    }

    [Fact]
    public async Task Handle_GeneratesBulletinNumber()
    {
        // Arrange
        var clarificationIds = new List<Guid>();
        var clarifications = CreateAnsweredClarifications(2, out clarificationIds);
        var command = CreateValidCommand(clarificationIds);

        // Setup with existing bulletins to test sequential numbering
        var existingBulletins = new List<ClarificationBulletin>
        {
            new ClarificationBulletin
            {
                Id = Guid.NewGuid(),
                TenderId = _tenderId,
                BulletinNumber = 1,
                IssueDate = DateTime.UtcNow.AddDays(-5),
                PublishedBy = _currentUserId,
                PublishedAt = DateTime.UtcNow.AddDays(-5),
                CreatedAt = DateTime.UtcNow.AddDays(-5)
            },
            new ClarificationBulletin
            {
                Id = Guid.NewGuid(),
                TenderId = _tenderId,
                BulletinNumber = 2,
                IssueDate = DateTime.UtcNow.AddDays(-2),
                PublishedBy = _currentUserId,
                PublishedAt = DateTime.UtcNow.AddDays(-2),
                CreatedAt = DateTime.UtcNow.AddDays(-2)
            }
        };

        SetupFullValidScenario(clarifications, existingBulletins);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        _bulletinsStore.Should().HaveCount(1);
        _bulletinsStore[0].BulletinNumber.Should().Be(3); // Next after existing 1 and 2
        result.BulletinNumber.Should().Be(3);
    }

    [Fact]
    public async Task Handle_GeneratesPdf()
    {
        // Arrange
        var clarificationIds = new List<Guid>();
        var clarifications = CreateAnsweredClarifications(2, out clarificationIds);
        var command = CreateValidCommand(clarificationIds);

        SetupFullValidScenario(clarifications);

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _pdfServiceMock.Verify(
            x => x.GenerateBulletinPdfAsync(
                It.IsAny<ClarificationBulletin>(),
                It.IsAny<Tender>(),
                It.IsAny<IEnumerable<Clarification>>(),
                It.IsAny<CancellationToken>()),
            Times.Once);

        _fileStorageServiceMock.Verify(
            x => x.UploadFileAsync(
                It.IsAny<Stream>(),
                It.Is<string>(f => f.EndsWith(".pdf")),
                It.Is<string>(ct => ct == "application/pdf"),
                It.Is<string>(p => p.Contains("Clarifications")),
                It.IsAny<CancellationToken>()),
            Times.Once);

        _bulletinsStore[0].PdfPath.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var clarificationIds = new List<Guid>();
        var clarifications = CreateAnsweredClarifications(2, out clarificationIds);
        var command = CreateValidCommand(clarificationIds);

        SetupFullValidScenario(clarifications);

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        // The handler calls SaveChangesAsync twice: once after creating the bulletin
        // and updating clarifications, once after sending emails and logging them.
        _contextMock.Verify(
            x => x.SaveChangesAsync(It.IsAny<CancellationToken>()),
            Times.Exactly(2));
    }

    [Fact]
    public async Task Handle_ReturnsBulletinDto()
    {
        // Arrange
        var clarificationIds = new List<Guid>();
        var clarifications = CreateAnsweredClarifications(2, out clarificationIds);
        var command = CreateValidCommand(clarificationIds);

        SetupFullValidScenario(clarifications);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.TenderId.Should().Be(_tenderId);
        result.BulletinNumber.Should().BeGreaterThan(0);
        result.Introduction.Should().Be(command.Introduction);
        result.ClosingNotes.Should().Be(command.ClosingNotes);
        result.PublishedBy.Should().Be(_currentUserId);
        result.PdfPath.Should().NotBeNullOrEmpty();
        result.QuestionCount.Should().Be(2);
        result.Questions.Should().HaveCount(2);
        result.Questions.Should().OnlyContain(q => !string.IsNullOrEmpty(q.ReferenceNumber));
        result.Questions.Should().OnlyContain(q => !string.IsNullOrEmpty(q.Answer));
    }

    [Fact]
    public async Task Handle_WithPdfGenerationFailure_ThrowsInvalidOperationException()
    {
        // Arrange
        var clarificationIds = new List<Guid>();
        var clarifications = CreateAnsweredClarifications(2, out clarificationIds);
        var command = CreateValidCommand(clarificationIds);

        SetupValidTender();
        SetupClarificationsDbSetForQuery(clarifications);
        SetupBulletinsDbSet(new List<ClarificationBulletin>());
        SetupBulletinsAdd();

        _pdfServiceMock.Setup(x => x.GenerateBulletinPdfAsync(
                It.IsAny<ClarificationBulletin>(),
                It.IsAny<Tender>(),
                It.IsAny<IEnumerable<Clarification>>(),
                It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("PDF generation failed"));

        // Act
        var act = () => _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*Failed to generate bulletin PDF*");
    }

    [Fact]
    public async Task Handle_WithMissingClarifications_ThrowsValidationException()
    {
        // Arrange
        var existingClarId = Guid.NewGuid();
        var missingClarId = Guid.NewGuid();
        var command = new PublishBulletinCommand
        {
            TenderId = _tenderId,
            ClarificationIds = new List<Guid> { existingClarId, missingClarId },
            Introduction = "Test",
            ClosingNotes = "Test"
        };

        var clarifications = new List<Clarification>
        {
            CreateClarification(existingClarId, ClarificationStatus.Answered, "CL-001")
        };

        SetupValidTender();
        SetupClarificationsDbSetForQuery(clarifications);

        // Act
        var act = () => _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<ValidationException>()
            .WithMessage("*not found*");
    }

    #region Helper Methods

    private PublishBulletinCommand CreateValidCommand(List<Guid> clarificationIds)
    {
        return new PublishBulletinCommand
        {
            TenderId = _tenderId,
            ClarificationIds = clarificationIds,
            Introduction = "This bulletin addresses questions received during the clarification period.",
            ClosingNotes = "Bidders are advised to incorporate these clarifications into their submissions."
        };
    }

    private List<Clarification> CreateAnsweredClarifications(
        int count,
        out List<Guid> clarificationIds)
    {
        clarificationIds = new List<Guid>();
        var clarifications = new List<Clarification>();

        for (int i = 1; i <= count; i++)
        {
            var id = Guid.NewGuid();
            clarificationIds.Add(id);
            clarifications.Add(CreateClarification(
                id,
                ClarificationStatus.Answered,
                $"CL-{i:D3}"));
        }

        return clarifications;
    }

    private List<Clarification> CreateClarificationsWithMixedStatuses(
        out List<Guid> clarificationIds)
    {
        clarificationIds = new List<Guid>();
        var clarifications = new List<Clarification>();

        // One answered, one still submitted
        var answeredId = Guid.NewGuid();
        var submittedId = Guid.NewGuid();

        clarificationIds.Add(answeredId);
        clarificationIds.Add(submittedId);

        clarifications.Add(CreateClarification(answeredId, ClarificationStatus.Answered, "CL-001"));
        clarifications.Add(CreateClarification(submittedId, ClarificationStatus.Submitted, "CL-002"));

        return clarifications;
    }

    private Clarification CreateClarification(
        Guid id,
        ClarificationStatus status,
        string referenceNumber)
    {
        return new Clarification
        {
            Id = id,
            TenderId = _tenderId,
            ReferenceNumber = referenceNumber,
            Subject = $"Question about {referenceNumber}",
            Question = "What are the specifications?",
            Answer = status == ClarificationStatus.Answered ? "The specifications are as follows..." : null,
            Status = status,
            ClarificationType = ClarificationType.BidderQuestion,
            Priority = ClarificationPriority.Normal,
            SubmittedByBidderId = Guid.NewGuid(),
            IsAnonymous = false,
            SubmittedAt = DateTime.UtcNow.AddDays(-3),
            AnsweredAt = status == ClarificationStatus.Answered ? DateTime.UtcNow.AddDays(-1) : null,
            AnsweredBy = status == ClarificationStatus.Answered ? _currentUserId : null,
            CreatedAt = DateTime.UtcNow.AddDays(-3)
        };
    }

    private static Tender CreateTestTender(Guid tenderId)
    {
        return new Tender
        {
            Id = tenderId,
            Title = "Infrastructure Project Tender",
            Reference = "TND-001",
            Status = TenderStatus.Active,
            ClarificationDeadline = DateTime.UtcNow.AddDays(5),
            SubmissionDeadline = DateTime.UtcNow.AddDays(15),
            OpeningDate = DateTime.UtcNow.AddDays(16),
            IssueDate = DateTime.UtcNow.AddDays(-10),
            TenderType = TenderType.Open,
            BaseCurrency = "AED",
            TechnicalWeight = 40,
            CommercialWeight = 60,
            CreatedAt = DateTime.UtcNow.AddDays(-15)
        };
    }

    private void SetupFullValidScenario(
        List<Clarification> clarifications,
        List<ClarificationBulletin>? existingBulletins = null)
    {
        SetupValidTender();
        SetupClarificationsDbSetForQuery(clarifications);
        SetupBulletinsDbSet(existingBulletins ?? new List<ClarificationBulletin>());
        SetupBulletinsAdd();
        SetupEmailLogsAdd();
        SetupPdfGeneration();
        SetupFileStorage();
        SetupEmptyTenderBidders();
        SetupUsersDbSet();
        SetupSaveChanges();
    }

    private void SetupValidTender()
    {
        var tender = CreateTestTender(_tenderId);
        SetupTendersDbSet(new List<Tender> { tender });
    }

    private void SetupTendersDbSet(List<Tender> tenders)
    {
        var mockDbSet = tenders.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Tenders).Returns(mockDbSet.Object);
    }

    private void SetupClarificationsDbSetForQuery(List<Clarification> clarifications)
    {
        var mockDbSet = clarifications.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Clarifications).Returns(mockDbSet.Object);
    }

    private void SetupBulletinsDbSet(List<ClarificationBulletin> bulletins)
    {
        var mockDbSet = bulletins.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.ClarificationBulletins).Returns(mockDbSet.Object);
    }

    private void SetupBulletinsAdd()
    {
        // Override with a mock that supports Add callback while keeping queryable behavior
        _contextMock.Setup(x => x.ClarificationBulletins.Add(It.IsAny<ClarificationBulletin>()))
            .Callback<ClarificationBulletin>(b => _bulletinsStore.Add(b));
    }

    private void SetupEmailLogsAdd()
    {
        var emailLogsMock = new Mock<DbSet<EmailLog>>();
        emailLogsMock.Setup(x => x.Add(It.IsAny<EmailLog>()))
            .Callback<EmailLog>(e => _emailLogsStore.Add(e));
        _contextMock.Setup(x => x.EmailLogs).Returns(emailLogsMock.Object);
    }

    private void SetupPdfGeneration()
    {
        var pdfBytes = new byte[] { 0x25, 0x50, 0x44, 0x46 }; // %PDF header
        _pdfServiceMock.Setup(x => x.GenerateBulletinPdfAsync(
                It.IsAny<ClarificationBulletin>(),
                It.IsAny<Tender>(),
                It.IsAny<IEnumerable<Clarification>>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(pdfBytes);
    }

    private void SetupFileStorage()
    {
        _fileStorageServiceMock.Setup(x => x.UploadFileAsync(
                It.IsAny<Stream>(),
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync("tender-documents/test/Clarifications/TND-001_QB-001.pdf");
    }

    private void SetupEmptyTenderBidders()
    {
        var emptyBidders = new List<TenderBidder>().AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.TenderBidders).Returns(emptyBidders.Object);
    }

    private void SetupUsersDbSet()
    {
        var publisher = new User
        {
            Id = _currentUserId,
            FirstName = "Admin",
            LastName = "User",
            Email = "admin@bayan.com",
            Role = UserRole.TenderManager,
            IsActive = true,
            CreatedAt = DateTime.UtcNow.AddDays(-30)
        };

        var mockDbSet = new List<User> { publisher }.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Users).Returns(mockDbSet.Object);
    }

    private void SetupSaveChanges()
    {
        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);
    }

    #endregion
}
