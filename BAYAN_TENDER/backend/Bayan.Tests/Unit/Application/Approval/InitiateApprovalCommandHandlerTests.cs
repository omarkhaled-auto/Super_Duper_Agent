using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Approval.Commands.InitiateApproval;
using Bayan.Application.Features.Approval.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Approval;

/// <summary>
/// Unit tests for InitiateApprovalCommandHandler.
/// </summary>
public class InitiateApprovalCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<ICurrentUserService> _currentUserServiceMock;
    private readonly Mock<IEmailService> _emailServiceMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly Mock<ILogger<InitiateApprovalCommandHandler>> _loggerMock;
    private readonly InitiateApprovalCommandHandler _handler;

    private readonly Guid _currentUserId = Guid.NewGuid();
    private readonly List<ApprovalWorkflow> _workflowsStore;
    private readonly List<ApprovalLevel> _levelsStore;

    public InitiateApprovalCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _currentUserServiceMock = new Mock<ICurrentUserService>();
        _emailServiceMock = new Mock<IEmailService>();
        _mapperMock = new Mock<IMapper>();
        _loggerMock = new Mock<ILogger<InitiateApprovalCommandHandler>>();

        _workflowsStore = new List<ApprovalWorkflow>();
        _levelsStore = new List<ApprovalLevel>();

        _currentUserServiceMock.Setup(x => x.UserId).Returns(_currentUserId);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        _handler = new InitiateApprovalCommandHandler(
            _contextMock.Object,
            _currentUserServiceMock.Object,
            _emailServiceMock.Object,
            _mapperMock.Object,
            _loggerMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidData_CreatesWorkflow()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();
        var (tender, approvers, initiator) = SetupValidScenario(tenderId, approverIds);
        var command = CreateCommand(tenderId, approverIds);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.WorkflowId.Should().NotBeEmpty();
        result.Workflow.Should().NotBeNull();
        _workflowsStore.Should().HaveCount(1);
    }

    [Fact]
    public async Task Handle_WithNonExistentTender_ThrowsInvalidOperationException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();

        SetupTendersDbSet(new List<Tender>()); // No tenders
        SetupApprovalWorkflowsDbSet(new List<ApprovalWorkflow>());

        var command = CreateCommand(tenderId, approverIds);

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*Tender not found*");
    }

    [Fact]
    public async Task Handle_WithExistingActiveWorkflow_RemovesExistingAndCreatesNew()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();
        var (tender, approvers, initiator) = SetupValidScenario(tenderId, approverIds);

        // Add an existing workflow for the same tender
        var existingWorkflow = new ApprovalWorkflow
        {
            Id = Guid.NewGuid(),
            TenderId = tenderId,
            Status = ApprovalWorkflowStatus.Rejected,
            InitiatedBy = _currentUserId,
            InitiatedAt = DateTime.UtcNow.AddDays(-1),
            Levels = new List<ApprovalLevel>
            {
                new ApprovalLevel
                {
                    Id = Guid.NewGuid(),
                    LevelNumber = 1,
                    ApproverUserId = approverIds[0],
                    Status = ApprovalLevelStatus.Rejected
                }
            }
        };

        SetupApprovalWorkflowsDbSet(new List<ApprovalWorkflow> { existingWorkflow });

        var command = CreateCommand(tenderId, approverIds);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.WorkflowId.Should().NotBeEmpty();
        // Verify old workflow was removed
        _contextMock.Verify(x => x.ApprovalWorkflows.Remove(existingWorkflow), Times.Once);
    }

    [Fact]
    public async Task Handle_SetsStatusToInProgress()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();
        var (tender, approvers, initiator) = SetupValidScenario(tenderId, approverIds);
        var command = CreateCommand(tenderId, approverIds);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Workflow.Status.Should().Be(ApprovalWorkflowStatus.InProgress);
        _workflowsStore.Should().HaveCount(1);
        _workflowsStore[0].Status.Should().Be(ApprovalWorkflowStatus.InProgress);
    }

    [Fact]
    public async Task Handle_SetsCurrentLevelTo1()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();
        var (tender, approvers, initiator) = SetupValidScenario(tenderId, approverIds);
        var command = CreateCommand(tenderId, approverIds);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Workflow.CurrentLevel.Should().Be(1);
    }

    [Fact]
    public async Task Handle_CreatesApprovalLevels()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();
        var (tender, approvers, initiator) = SetupValidScenario(tenderId, approverIds);
        var command = CreateCommand(tenderId, approverIds);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Workflow.Levels.Should().HaveCount(3);
        result.Workflow.TotalLevels.Should().Be(3);

        // Level 1 should be Active, levels 2 and 3 should be Waiting
        var levels = result.Workflow.Levels.OrderBy(l => l.LevelNumber).ToList();
        levels[0].LevelNumber.Should().Be(1);
        levels[0].Status.Should().Be(ApprovalLevelStatus.Active);
        levels[1].LevelNumber.Should().Be(2);
        levels[1].Status.Should().Be(ApprovalLevelStatus.Waiting);
        levels[2].LevelNumber.Should().Be(3);
        levels[2].Status.Should().Be(ApprovalLevelStatus.Waiting);
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();
        var (tender, approvers, initiator) = SetupValidScenario(tenderId, approverIds);
        var command = CreateCommand(tenderId, approverIds);

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        // Called once for removing existing workflow (if any) and once after creating new workflow
        _contextMock.Verify(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.AtLeastOnce);
    }

    [Fact]
    public async Task Handle_SetsInitiatedByCurrentUser()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();
        var (tender, approvers, initiator) = SetupValidScenario(tenderId, approverIds);
        var command = CreateCommand(tenderId, approverIds);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Workflow.InitiatedBy.Should().Be(_currentUserId);
        _workflowsStore.Should().HaveCount(1);
        _workflowsStore[0].InitiatedBy.Should().Be(_currentUserId);
    }

    [Fact]
    public async Task Handle_WithUnauthenticatedUser_ThrowsUnauthorizedAccessException()
    {
        // Arrange
        _currentUserServiceMock.Setup(x => x.UserId).Returns((Guid?)null);

        var handler = new InitiateApprovalCommandHandler(
            _contextMock.Object,
            _currentUserServiceMock.Object,
            _emailServiceMock.Object,
            _mapperMock.Object,
            _loggerMock.Object);

        var command = CreateCommand(Guid.NewGuid(), CreateApproverIds());

        // Act
        var act = async () => await handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<UnauthorizedAccessException>()
            .WithMessage("*authenticated*");
    }

    [Fact]
    public async Task Handle_ReturnsWorkflowDto()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var approverIds = CreateApproverIds();
        var (tender, approvers, initiator) = SetupValidScenario(tenderId, approverIds);
        var command = CreateCommand(tenderId, approverIds);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Workflow.Should().NotBeNull();
        result.Workflow.Should().BeOfType<ApprovalWorkflowDto>();
        result.Workflow.TenderId.Should().Be(tenderId);
        result.Workflow.TenderReference.Should().Be(tender.Reference);
        result.Workflow.TenderTitle.Should().Be(tender.Title);
        result.Workflow.Status.Should().Be(ApprovalWorkflowStatus.InProgress);
        result.Workflow.Levels.Should().NotBeEmpty();
        result.Workflow.Levels.Should().HaveCount(3);

        // Verify approver information is populated
        foreach (var level in result.Workflow.Levels)
        {
            level.ApproverName.Should().NotBeNullOrEmpty();
            level.ApproverEmail.Should().NotBeNullOrEmpty();
        }
    }

    #region Helper Methods

    private static List<Guid> CreateApproverIds()
    {
        return new List<Guid> { Guid.NewGuid(), Guid.NewGuid(), Guid.NewGuid() };
    }

    private static InitiateApprovalCommand CreateCommand(Guid tenderId, List<Guid> approverIds)
    {
        return new InitiateApprovalCommand
        {
            TenderId = tenderId,
            ApproverUserIds = approverIds,
            AwardPackPdfPath = "/uploads/award-pack.pdf"
        };
    }

    private (Tender tender, List<User> approvers, User initiator) SetupValidScenario(
        Guid tenderId, List<Guid> approverIds)
    {
        var client = new Client
        {
            Id = Guid.NewGuid(),
            Name = "Test Client",
            CreatedAt = DateTime.UtcNow
        };

        var tender = new Tender
        {
            Id = tenderId,
            Title = "Test Tender",
            Reference = "TND-001",
            ClientId = client.Id,
            Client = client,
            Status = TenderStatus.Active,
            CreatedAt = DateTime.UtcNow
        };

        var approvers = approverIds.Select((id, index) => new User
        {
            Id = id,
            FirstName = $"Approver{index + 1}",
            LastName = "Test",
            Email = $"approver{index + 1}@example.com",
            Role = UserRole.Approver,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        }).ToList();

        var initiator = new User
        {
            Id = _currentUserId,
            FirstName = "Initiator",
            LastName = "Test",
            Email = "initiator@example.com",
            Role = UserRole.TenderManager,
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };

        var allUsers = new List<User>(approvers) { initiator };

        SetupTendersDbSet(new List<Tender> { tender });
        SetupApprovalWorkflowsDbSet(new List<ApprovalWorkflow>());
        SetupUsersDbSet(allUsers);
        SetupApprovalLevelsDbSet();
        SetupWorkflowsAdd();

        return (tender, approvers, initiator);
    }

    private void SetupTendersDbSet(List<Tender> tenders)
    {
        var mockDbSet = tenders.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Tenders).Returns(mockDbSet.Object);
    }

    private void SetupApprovalWorkflowsDbSet(List<ApprovalWorkflow> workflows)
    {
        var mockDbSet = workflows.AsQueryable().BuildMockDbSet();

        mockDbSet.Setup(x => x.Add(It.IsAny<ApprovalWorkflow>()))
            .Callback<ApprovalWorkflow>(wf => _workflowsStore.Add(wf));

        mockDbSet.Setup(x => x.Remove(It.IsAny<ApprovalWorkflow>()));

        _contextMock.Setup(x => x.ApprovalWorkflows).Returns(mockDbSet.Object);
    }

    private void SetupUsersDbSet(List<User> users)
    {
        var mockDbSet = users.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Users).Returns(mockDbSet.Object);
    }

    private void SetupApprovalLevelsDbSet()
    {
        var mockDbSet = new Mock<DbSet<ApprovalLevel>>();

        mockDbSet.Setup(x => x.Add(It.IsAny<ApprovalLevel>()))
            .Callback<ApprovalLevel>(level => _levelsStore.Add(level));

        mockDbSet.Setup(x => x.RemoveRange(It.IsAny<IEnumerable<ApprovalLevel>>()));

        _contextMock.Setup(x => x.ApprovalLevels).Returns(mockDbSet.Object);
    }

    private void SetupWorkflowsAdd()
    {
        // Ensure the Add on the workflow DbSet stores the workflow
        // This is set in SetupApprovalWorkflowsDbSet but we ensure it here as well
    }

    #endregion
}
