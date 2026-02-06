using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Approval.Commands.SubmitApprovalDecision;
using Bayan.Application.Features.Approval.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.Extensions.Logging;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Approval;

/// <summary>
/// Unit tests for SubmitApprovalDecisionCommandHandler.
/// </summary>
public class SubmitApprovalDecisionCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<ICurrentUserService> _currentUserServiceMock;
    private readonly Mock<IEmailService> _emailServiceMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly Mock<ILogger<SubmitApprovalDecisionCommandHandler>> _loggerMock;
    private readonly SubmitApprovalDecisionCommandHandler _handler;

    private readonly Guid _currentUserId = Guid.NewGuid();

    public SubmitApprovalDecisionCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _currentUserServiceMock = new Mock<ICurrentUserService>();
        _emailServiceMock = new Mock<IEmailService>();
        _mapperMock = new Mock<IMapper>();
        _loggerMock = new Mock<ILogger<SubmitApprovalDecisionCommandHandler>>();

        _currentUserServiceMock.Setup(x => x.UserId).Returns(_currentUserId);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        _handler = new SubmitApprovalDecisionCommandHandler(
            _contextMock.Object,
            _currentUserServiceMock.Object,
            _emailServiceMock.Object,
            _mapperMock.Object,
            _loggerMock.Object);
    }

    [Fact]
    public async Task Handle_WithApproval_AdvancesToNextLevel()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 1);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = "Approved at Level 1"
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Success.Should().BeTrue();
        result.IsWorkflowComplete.Should().BeFalse();
        result.Message.Should().Contain("Level 2");

        // Level 1 should be approved, Level 2 should become active
        var level1 = workflow.Levels.First(l => l.LevelNumber == 1);
        level1.Status.Should().Be(ApprovalLevelStatus.Approved);

        var level2 = workflow.Levels.First(l => l.LevelNumber == 2);
        level2.Status.Should().Be(ApprovalLevelStatus.Active);
    }

    [Fact]
    public async Task Handle_WithFinalApproval_CompletesWorkflow()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 3);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = "Final approval granted"
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Success.Should().BeTrue();
        result.IsWorkflowComplete.Should().BeTrue();
        result.Message.Should().Contain("Final approval");

        workflow.Status.Should().Be(ApprovalWorkflowStatus.Approved);
        workflow.CompletedAt.Should().NotBeNull();
        workflow.Tender.Status.Should().Be(TenderStatus.Awarded);
    }

    [Fact]
    public async Task Handle_WithRejection_RejectsWorkflow()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 1);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Reject,
            Comment = "Rejected due to budget constraints"
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Success.Should().BeTrue();
        result.IsWorkflowComplete.Should().BeTrue();
        result.Message.Should().Contain("rejected");

        workflow.Status.Should().Be(ApprovalWorkflowStatus.Rejected);
        workflow.CompletedAt.Should().NotBeNull();

        // All waiting levels should be rejected
        workflow.Levels
            .Where(l => l.LevelNumber > 1)
            .All(l => l.Status == ApprovalLevelStatus.Rejected)
            .Should().BeTrue();
    }

    [Fact]
    public async Task Handle_WithReturnForRevision_ReturnsWorkflow()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 2);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.ReturnForRevision,
            Comment = "Please revise the commercial analysis"
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Success.Should().BeTrue();
        result.IsWorkflowComplete.Should().BeTrue();
        result.Message.Should().Contain("revision");

        workflow.Status.Should().Be(ApprovalWorkflowStatus.RevisionNeeded);
        workflow.CompletedAt.Should().NotBeNull();

        // Remaining waiting levels should be returned
        var level3 = workflow.Levels.First(l => l.LevelNumber == 3);
        level3.Status.Should().Be(ApprovalLevelStatus.Returned);
    }

    [Fact]
    public async Task Handle_WithNonExistentWorkflow_ThrowsInvalidOperationException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();

        SetupApprovalWorkflowsDbSet(new List<ApprovalWorkflow>()); // No workflows
        SetupUsersDbSet(new List<User>());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = "Approved"
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*No active approval workflow*");
    }

    [Fact]
    public async Task Handle_WithUnauthorizedUser_ThrowsUnauthorizedAccessException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var differentUserId = Guid.NewGuid();

        // Create a workflow where the active level's approver is a different user
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 1, specificApproverForActiveLevel: differentUserId);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = "Approved"
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<UnauthorizedAccessException>()
            .WithMessage("*not authorized*");
    }

    [Fact]
    public async Task Handle_SetsDecisionTimestamp()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var beforeTest = DateTime.UtcNow;
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 1);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = "Approved"
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);
        var afterTest = DateTime.UtcNow;

        // Assert
        var activeLevel = workflow.Levels.First(l => l.LevelNumber == 1);
        activeLevel.DecidedAt.Should().NotBeNull();
        activeLevel.DecidedAt.Should().BeOnOrAfter(beforeTest);
        activeLevel.DecidedAt.Should().BeOnOrBefore(afterTest);
    }

    [Fact]
    public async Task Handle_SetsDecisionComment()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 1);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var expectedComment = "Approved with conditions - please review budget";

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = expectedComment
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        var activeLevel = workflow.Levels.First(l => l.LevelNumber == 1);
        activeLevel.DecisionComment.Should().Be(expectedComment);
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 1);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = "Approved"
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _contextMock.Verify(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.AtLeastOnce);
    }

    [Fact]
    public async Task Handle_WithCompletedWorkflow_ThrowsInvalidOperationException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();

        // Create a completed (Approved) workflow - handler searches for InProgress only
        var initiator = CreateTestUser(_currentUserId, "initiator@example.com", "Initiator", "Test");
        var client = new Client { Id = Guid.NewGuid(), Name = "Test Client", CreatedAt = DateTime.UtcNow };
        var tender = CreateTestTender(tenderId, client);

        var approver1Id = Guid.NewGuid();
        var completedWorkflow = new ApprovalWorkflow
        {
            Id = Guid.NewGuid(),
            TenderId = tenderId,
            Status = ApprovalWorkflowStatus.Approved, // Already completed
            InitiatedBy = _currentUserId,
            InitiatedAt = DateTime.UtcNow.AddDays(-3),
            CompletedAt = DateTime.UtcNow.AddDays(-1),
            Tender = tender,
            Initiator = initiator,
            Levels = new List<ApprovalLevel>
            {
                new ApprovalLevel
                {
                    Id = Guid.NewGuid(),
                    LevelNumber = 1,
                    ApproverUserId = approver1Id,
                    Status = ApprovalLevelStatus.Approved,
                    Decision = ApprovalDecision.Approve
                }
            }
        };

        // Only InProgress workflows are found by the handler query
        SetupApprovalWorkflowsDbSet(new List<ApprovalWorkflow> { completedWorkflow });
        SetupUsersDbSet(new List<User> { initiator });

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = "Trying to approve completed workflow"
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*No active approval workflow*");
    }

    [Fact]
    public async Task Handle_ReturnsUpdatedWorkflowDto()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var (workflow, approverUsers) = SetupWorkflowWithActiveLevel(tenderId, 1);
        SetupUsersDbSet(approverUsers.Values.ToList());

        var command = new SubmitApprovalDecisionCommand
        {
            TenderId = tenderId,
            Decision = ApprovalDecision.Approve,
            Comment = "Looks good"
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Workflow.Should().NotBeNull();
        result.Workflow.Should().BeOfType<ApprovalWorkflowDto>();
        result.Workflow.TenderId.Should().Be(tenderId);
        result.Workflow.Levels.Should().NotBeEmpty();
        result.Success.Should().BeTrue();
        result.Message.Should().NotBeNullOrEmpty();
    }

    #region Helper Methods

    private static User CreateTestUser(Guid id, string email, string firstName, string lastName)
    {
        return new User
        {
            Id = id,
            Email = email,
            FirstName = firstName,
            LastName = lastName,
            Role = UserRole.Approver,
            IsActive = true,
            PasswordHash = "hash",
            CreatedAt = DateTime.UtcNow
        };
    }

    private static Tender CreateTestTender(Guid tenderId, Client client)
    {
        return new Tender
        {
            Id = tenderId,
            Title = "Test Tender for Approval",
            Reference = "TND-APR-001",
            ClientId = client.Id,
            Client = client,
            Status = TenderStatus.Evaluation,
            CreatedAt = DateTime.UtcNow
        };
    }

    /// <summary>
    /// Creates a workflow with 3 levels where the specified level is active.
    /// For the active level, the current user is set as the approver (unless overridden).
    /// </summary>
    private (ApprovalWorkflow workflow, Dictionary<Guid, User> approverUsers) SetupWorkflowWithActiveLevel(
        Guid tenderId,
        int activeLevelNumber,
        Guid? specificApproverForActiveLevel = null)
    {
        var initiatorId = Guid.NewGuid();
        var initiator = CreateTestUser(initiatorId, "initiator@example.com", "Initiator", "Test");

        var client = new Client { Id = Guid.NewGuid(), Name = "Test Client", CreatedAt = DateTime.UtcNow };
        var tender = CreateTestTender(tenderId, client);

        var approverUsers = new Dictionary<Guid, User>();
        var levels = new List<ApprovalLevel>();

        for (int i = 1; i <= 3; i++)
        {
            Guid approverId;

            if (i == activeLevelNumber)
            {
                approverId = specificApproverForActiveLevel ?? _currentUserId;
            }
            else
            {
                approverId = Guid.NewGuid();
            }

            var approver = CreateTestUser(approverId, $"approver{i}@example.com", $"Approver{i}", "Test");
            approverUsers[approverId] = approver;

            ApprovalLevelStatus status;
            if (i < activeLevelNumber)
            {
                status = ApprovalLevelStatus.Approved;
            }
            else if (i == activeLevelNumber)
            {
                status = ApprovalLevelStatus.Active;
            }
            else
            {
                status = ApprovalLevelStatus.Waiting;
            }

            levels.Add(new ApprovalLevel
            {
                Id = Guid.NewGuid(),
                LevelNumber = i,
                ApproverUserId = approverId,
                Status = status,
                Decision = i < activeLevelNumber ? ApprovalDecision.Approve : null,
                DecidedAt = i < activeLevelNumber ? DateTime.UtcNow.AddDays(-1) : null,
                CreatedAt = DateTime.UtcNow
            });
        }

        // Add initiator to the users dictionary
        approverUsers[initiatorId] = initiator;

        var workflow = new ApprovalWorkflow
        {
            Id = Guid.NewGuid(),
            TenderId = tenderId,
            Status = ApprovalWorkflowStatus.InProgress,
            InitiatedBy = initiatorId,
            InitiatedAt = DateTime.UtcNow.AddDays(-2),
            Tender = tender,
            Initiator = initiator,
            Levels = levels,
            CreatedAt = DateTime.UtcNow
        };

        // Set WorkflowId on all levels
        foreach (var level in levels)
        {
            level.WorkflowId = workflow.Id;
        }

        SetupApprovalWorkflowsDbSet(new List<ApprovalWorkflow> { workflow });

        return (workflow, approverUsers);
    }

    private void SetupApprovalWorkflowsDbSet(List<ApprovalWorkflow> workflows)
    {
        var mockDbSet = workflows.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.ApprovalWorkflows).Returns(mockDbSet.Object);
    }

    private void SetupUsersDbSet(List<User> users)
    {
        var mockDbSet = users.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Users).Returns(mockDbSet.Object);
    }

    #endregion
}
