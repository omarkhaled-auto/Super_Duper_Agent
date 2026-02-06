using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Auth.Commands.Login;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Auth;

/// <summary>
/// Unit tests for LoginCommandHandler.
/// </summary>
public class LoginCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IPasswordHasher> _passwordHasherMock;
    private readonly Mock<IJwtTokenService> _jwtTokenServiceMock;
    private readonly LoginCommandHandler _handler;

    public LoginCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _passwordHasherMock = new Mock<IPasswordHasher>();
        _jwtTokenServiceMock = new Mock<IJwtTokenService>();

        _jwtTokenServiceMock.Setup(x => x.AccessTokenExpirationMinutes).Returns(60);
        _jwtTokenServiceMock.Setup(x => x.RefreshTokenExpirationDays).Returns(7);

        _handler = new LoginCommandHandler(
            _contextMock.Object,
            _passwordHasherMock.Object,
            _jwtTokenServiceMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidCredentials_ReturnsLoginResponseWithTokens()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "ValidPassword123!";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        var users = new List<User> { user };

        SetupUsersDbSet(users);
        SetupRefreshTokensDbSet(new List<RefreshToken>());

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(true);
        _jwtTokenServiceMock.Setup(x => x.GenerateAccessToken(It.IsAny<User>()))
            .Returns("test-access-token");
        _jwtTokenServiceMock.Setup(x => x.GenerateRefreshToken())
            .Returns("test-refresh-token");

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = false,
            IpAddress = "127.0.0.1"
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.AccessToken.Should().Be("test-access-token");
        result.RefreshToken.Should().Be("test-refresh-token");
        result.TokenType.Should().Be("Bearer");
        result.User.Should().NotBeNull();
        result.User.Id.Should().Be(userId);
        result.User.Email.Should().Be(email);
    }

    [Fact]
    public async Task Handle_WithInvalidPassword_ThrowsUnauthorizedAccessException()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "WrongPassword";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        var users = new List<User> { user };

        SetupUsersDbSet(users);

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(false);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<UnauthorizedAccessException>()
            .WithMessage("Invalid email or password.");
    }

    [Fact]
    public async Task Handle_WithNonExistentUser_ThrowsUnauthorizedAccessException()
    {
        // Arrange
        var users = new List<User>();
        SetupUsersDbSet(users);

        var command = new LoginCommand
        {
            Email = "nonexistent@example.com",
            Password = "AnyPassword",
            RememberMe = false
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<UnauthorizedAccessException>()
            .WithMessage("Invalid email or password.");
    }

    [Fact]
    public async Task Handle_WithInactiveUser_ThrowsUnauthorizedAccessException()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "ValidPassword123!";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: false);
        var users = new List<User> { user };

        SetupUsersDbSet(users);

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(true);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<UnauthorizedAccessException>()
            .WithMessage("Your account has been deactivated. Please contact support.");
    }

    [Fact]
    public async Task Handle_WithLockedAccount_ThrowsUnauthorizedAccessException()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        user.LockoutEnd = DateTime.UtcNow.AddMinutes(10); // Account is locked for 10 more minutes

        var users = new List<User> { user };
        SetupUsersDbSet(users);

        var command = new LoginCommand
        {
            Email = email,
            Password = "AnyPassword",
            RememberMe = false
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<UnauthorizedAccessException>()
            .WithMessage("Account is locked.*");
    }

    [Fact]
    public async Task Handle_WithValidCredentials_GeneratesJwtTokenCorrectly()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "ValidPassword123!";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        var users = new List<User> { user };

        SetupUsersDbSet(users);
        SetupRefreshTokensDbSet(new List<RefreshToken>());

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(true);

        var expectedAccessToken = "jwt.access.token";
        _jwtTokenServiceMock.Setup(x => x.GenerateAccessToken(It.Is<User>(u => u.Id == userId)))
            .Returns(expectedAccessToken);
        _jwtTokenServiceMock.Setup(x => x.GenerateRefreshToken())
            .Returns("refresh-token");

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.AccessToken.Should().Be(expectedAccessToken);
        _jwtTokenServiceMock.Verify(x => x.GenerateAccessToken(It.Is<User>(u => u.Id == userId)), Times.Once);
        _jwtTokenServiceMock.Verify(x => x.GenerateRefreshToken(), Times.Once);
    }

    [Fact]
    public async Task Handle_WithRememberMe_SetsLongerRefreshTokenExpiry()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "ValidPassword123!";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        var users = new List<User> { user };

        SetupUsersDbSet(users);
        SetupRefreshTokensDbSet(new List<RefreshToken>());

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(true);
        _jwtTokenServiceMock.Setup(x => x.GenerateAccessToken(It.IsAny<User>()))
            .Returns("test-access-token");
        _jwtTokenServiceMock.Setup(x => x.GenerateRefreshToken())
            .Returns("test-refresh-token");

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = true,
            IpAddress = "127.0.0.1"
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        // With RememberMe = true, refresh token should expire in 30 days
        var expectedExpiry = DateTime.UtcNow.AddDays(30);
        result.RefreshTokenExpiresAt.Should().BeCloseTo(expectedExpiry, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_WithInvalidPassword_IncrementsFailedLoginAttempts()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "WrongPassword";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        user.FailedLoginAttempts = 0;

        var users = new List<User> { user };
        SetupUsersDbSet(users);

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(false);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act & Assert
        await Assert.ThrowsAsync<UnauthorizedAccessException>(() =>
            _handler.Handle(command, CancellationToken.None));

        user.FailedLoginAttempts.Should().Be(1);
    }

    [Fact]
    public async Task Handle_WithFiveFailedAttempts_LocksAccount()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "WrongPassword";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        user.FailedLoginAttempts = 4; // One more failed attempt will lock the account

        var users = new List<User> { user };
        SetupUsersDbSet(users);

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(false);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act & Assert
        await Assert.ThrowsAsync<UnauthorizedAccessException>(() =>
            _handler.Handle(command, CancellationToken.None));

        user.FailedLoginAttempts.Should().Be(5);
        user.LockoutEnd.Should().NotBeNull();
        user.LockoutEnd.Should().BeCloseTo(DateTime.UtcNow.AddMinutes(15), TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_WithSuccessfulLogin_ResetsFailedLoginAttempts()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "ValidPassword123!";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        user.FailedLoginAttempts = 3;

        var users = new List<User> { user };
        SetupUsersDbSet(users);
        SetupRefreshTokensDbSet(new List<RefreshToken>());

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(true);
        _jwtTokenServiceMock.Setup(x => x.GenerateAccessToken(It.IsAny<User>()))
            .Returns("test-access-token");
        _jwtTokenServiceMock.Setup(x => x.GenerateRefreshToken())
            .Returns("test-refresh-token");

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        user.FailedLoginAttempts.Should().Be(0);
        user.LockoutEnd.Should().BeNull();
    }

    [Fact]
    public async Task Handle_WithSuccessfulLogin_UpdatesLastLoginAt()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "test@example.com";
        var password = "ValidPassword123!";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, email, passwordHash, isActive: true);
        user.LastLoginAt = null;

        var users = new List<User> { user };
        SetupUsersDbSet(users);
        SetupRefreshTokensDbSet(new List<RefreshToken>());

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(true);
        _jwtTokenServiceMock.Setup(x => x.GenerateAccessToken(It.IsAny<User>()))
            .Returns("test-access-token");
        _jwtTokenServiceMock.Setup(x => x.GenerateRefreshToken())
            .Returns("test-refresh-token");

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email,
            Password = password,
            RememberMe = false
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        user.LastLoginAt.Should().NotBeNull();
        user.LastLoginAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_WithCaseInsensitiveEmail_FindsUser()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var email = "Test@Example.COM";
        var password = "ValidPassword123!";
        var passwordHash = "$2a$12$HashedPassword";

        var user = CreateTestUser(userId, "test@example.com", passwordHash, isActive: true);
        var users = new List<User> { user };

        SetupUsersDbSet(users);
        SetupRefreshTokensDbSet(new List<RefreshToken>());

        _passwordHasherMock.Setup(x => x.VerifyPassword(password, passwordHash))
            .Returns(true);
        _jwtTokenServiceMock.Setup(x => x.GenerateAccessToken(It.IsAny<User>()))
            .Returns("test-access-token");
        _jwtTokenServiceMock.Setup(x => x.GenerateRefreshToken())
            .Returns("test-refresh-token");

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        var command = new LoginCommand
        {
            Email = email.ToUpper(), // Using uppercase
            Password = password,
            RememberMe = false
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.User.Should().NotBeNull();
    }

    private static User CreateTestUser(Guid id, string email, string passwordHash, bool isActive)
    {
        return new User
        {
            Id = id,
            Email = email,
            PasswordHash = passwordHash,
            FirstName = "Test",
            LastName = "User",
            Role = UserRole.Admin,
            IsActive = isActive,
            EmailVerified = true,
            FailedLoginAttempts = 0,
            LockoutEnd = null,
            CreatedAt = DateTime.UtcNow.AddDays(-30)
        };
    }

    private void SetupUsersDbSet(List<User> users)
    {
        var mockDbSet = users.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Users).Returns(mockDbSet.Object);
    }

    private void SetupRefreshTokensDbSet(List<RefreshToken> refreshTokens)
    {
        var mockDbSet = refreshTokens.AsQueryable().BuildMockDbSet();

        mockDbSet.Setup(x => x.Add(It.IsAny<RefreshToken>()))
            .Callback<RefreshToken>(token => refreshTokens.Add(token));

        _contextMock.Setup(x => x.RefreshTokens).Returns(mockDbSet.Object);
    }
}
