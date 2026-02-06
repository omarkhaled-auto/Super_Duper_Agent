using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Admin.Users.Commands.CreateUser;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Moq;

namespace Bayan.Tests.Unit.Application.Users;

/// <summary>
/// Unit tests for CreateUserCommandHandler.
/// </summary>
public class CreateUserCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IPasswordHasher> _passwordHasherMock;
    private readonly Mock<IEmailService> _emailServiceMock;
    private readonly Mock<ILogger<CreateUserCommandHandler>> _loggerMock;
    private readonly CreateUserCommandHandler _handler;
    private readonly List<User> _usersStore;

    public CreateUserCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _passwordHasherMock = new Mock<IPasswordHasher>();
        _emailServiceMock = new Mock<IEmailService>();
        _loggerMock = new Mock<ILogger<CreateUserCommandHandler>>();
        _usersStore = new List<User>();

        SetupUsersDbSet();

        _handler = new CreateUserCommandHandler(
            _contextMock.Object,
            _passwordHasherMock.Object,
            _emailServiceMock.Object,
            _loggerMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidCommand_CreatesUserSuccessfully()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            Phone = "+966501234567",
            CompanyName = "Test Company",
            Department = "IT",
            JobTitle = "Manager",
            SendInvitationEmail = false
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.UserId.Should().NotBeEmpty();
        result.TemporaryPassword.Should().Be(temporaryPassword); // Returned since email was not sent
        result.InvitationEmailSent.Should().BeFalse();
    }

    [Fact]
    public async Task Handle_WithValidCommand_HashesPasswordBeforeStorage()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            SendInvitationEmail = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _passwordHasherMock.Verify(x => x.GenerateTemporaryPassword(It.IsAny<int>()), Times.Once);
        _passwordHasherMock.Verify(x => x.HashPassword(temporaryPassword), Times.Once);

        // Verify that the user added to the context has the hashed password
        _usersStore.Should().HaveCount(1);
        _usersStore[0].PasswordHash.Should().Be(passwordHash);
    }

    [Fact]
    public async Task Handle_WithSendInvitationEmailTrue_SendsInvitationEmail()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _emailServiceMock.Setup(x => x.SendUserInvitationEmailAsync(
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            SendInvitationEmail = true
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.InvitationEmailSent.Should().BeTrue();
        result.TemporaryPassword.Should().BeNull(); // Not returned when email is sent

        _emailServiceMock.Verify(x => x.SendUserInvitationEmailAsync(
            "john.doe@example.com",
            "John",
            temporaryPassword,
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task Handle_WithSendInvitationEmailFalse_DoesNotSendEmail()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            SendInvitationEmail = false
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.InvitationEmailSent.Should().BeFalse();
        result.TemporaryPassword.Should().Be(temporaryPassword);

        _emailServiceMock.Verify(x => x.SendUserInvitationEmailAsync(
            It.IsAny<string>(),
            It.IsAny<string>(),
            It.IsAny<string>(),
            It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task Handle_WhenEmailServiceFails_ReturnsTemporaryPassword()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _emailServiceMock.Setup(x => x.SendUserInvitationEmailAsync(
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<CancellationToken>()))
            .ThrowsAsync(new Exception("Email service unavailable"));

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            SendInvitationEmail = true
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.InvitationEmailSent.Should().BeFalse();
        result.TemporaryPassword.Should().Be(temporaryPassword); // Returned since email failed
        result.UserId.Should().NotBeEmpty(); // User should still be created
    }

    [Fact]
    public async Task Handle_WithValidCommand_SetsUserPropertiesCorrectly()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = " John ", // With whitespace
            LastName = " Doe ",
            Email = " John.Doe@Example.COM ", // With whitespace and mixed case
            Role = UserRole.CommercialAnalyst,
            Phone = " +966501234567 ",
            CompanyName = " Test Company ",
            Department = " Finance ",
            JobTitle = " Analyst ",
            SendInvitationEmail = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _usersStore.Should().HaveCount(1);
        var createdUser = _usersStore[0];

        createdUser.FirstName.Should().Be("John"); // Trimmed
        createdUser.LastName.Should().Be("Doe"); // Trimmed
        createdUser.Email.Should().Be("john.doe@example.com"); // Trimmed and lowercase
        createdUser.Role.Should().Be(UserRole.CommercialAnalyst);
        createdUser.PhoneNumber.Should().Be("+966501234567"); // Trimmed
        createdUser.CompanyName.Should().Be("Test Company"); // Trimmed
        createdUser.Department.Should().Be("Finance"); // Trimmed
        createdUser.JobTitle.Should().Be("Analyst"); // Trimmed
        createdUser.IsActive.Should().BeTrue();
        createdUser.EmailVerified.Should().BeFalse();
    }

    [Fact]
    public async Task Handle_WithValidCommand_GeneratesNewGuidForUserId()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            SendInvitationEmail = false
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.UserId.Should().NotBeEmpty();
        _usersStore[0].Id.Should().Be(result.UserId);
    }

    [Fact]
    public async Task Handle_WithValidCommand_SetsCreatedAtToUtcNow()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";
        var beforeTest = DateTime.UtcNow;

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            SendInvitationEmail = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);
        var afterTest = DateTime.UtcNow;

        // Assert
        _usersStore[0].CreatedAt.Should().BeOnOrAfter(beforeTest);
        _usersStore[0].CreatedAt.Should().BeOnOrBefore(afterTest);
    }

    [Fact]
    public async Task Handle_WithNullOptionalFields_SetsNullValues()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            Phone = null,
            CompanyName = null,
            Department = null,
            JobTitle = null,
            SendInvitationEmail = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _usersStore[0].PhoneNumber.Should().BeNull();
        _usersStore[0].CompanyName.Should().BeNull();
        _usersStore[0].Department.Should().BeNull();
        _usersStore[0].JobTitle.Should().BeNull();
    }

    [Theory]
    [InlineData(UserRole.Admin)]
    [InlineData(UserRole.TenderManager)]
    [InlineData(UserRole.CommercialAnalyst)]
    [InlineData(UserRole.TechnicalPanelist)]
    [InlineData(UserRole.Approver)]
    [InlineData(UserRole.Auditor)]
    [InlineData(UserRole.Bidder)]
    public async Task Handle_WithDifferentRoles_SetsRoleCorrectly(UserRole role)
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = $"john.doe.{role}@example.com",
            Role = role,
            SendInvitationEmail = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _usersStore.Last().Role.Should().Be(role);
    }

    [Fact]
    public async Task Handle_WithValidCommand_CallsSaveChangesAsync()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            Role = UserRole.TenderManager,
            SendInvitationEmail = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _contextMock.Verify(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task Handle_WithValidCommand_AddsUserToContext()
    {
        // Arrange
        var temporaryPassword = "TempPass123!";
        var passwordHash = "$2a$12$HashedPassword";

        _passwordHasherMock.Setup(x => x.GenerateTemporaryPassword(It.IsAny<int>()))
            .Returns(temporaryPassword);
        _passwordHasherMock.Setup(x => x.HashPassword(temporaryPassword))
            .Returns(passwordHash);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new CreateUserCommand
        {
            FirstName = "Jane",
            LastName = "Smith",
            Email = "jane.smith@example.com",
            Role = UserRole.Bidder,
            SendInvitationEmail = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _usersStore.Should().Contain(u => u.Email == "jane.smith@example.com");
    }

    private void SetupUsersDbSet()
    {
        var mockDbSet = new Mock<DbSet<User>>();

        mockDbSet.Setup(x => x.Add(It.IsAny<User>()))
            .Callback<User>(user => _usersStore.Add(user));

        _contextMock.Setup(x => x.Users).Returns(mockDbSet.Object);
    }
}
