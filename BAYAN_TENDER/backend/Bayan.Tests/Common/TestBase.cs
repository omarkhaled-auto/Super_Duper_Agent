using Bayan.Application.Common.Interfaces;
using Bayan.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Moq;

namespace Bayan.Tests.Common;

/// <summary>
/// Base class for unit tests providing common setup and utilities.
/// </summary>
public abstract class TestBase : IDisposable
{
    protected readonly ApplicationDbContext DbContext;
    protected readonly Mock<ICurrentUserService> CurrentUserServiceMock;
    protected readonly Mock<IDateTime> DateTimeServiceMock;

    protected TestBase()
    {
        // Setup mock for current user service
        CurrentUserServiceMock = new Mock<ICurrentUserService>();
        CurrentUserServiceMock.Setup(x => x.UserId).Returns(Guid.NewGuid());
        CurrentUserServiceMock.Setup(x => x.IsAuthenticated).Returns(true);
        CurrentUserServiceMock.Setup(x => x.Email).Returns("test@example.com");
        CurrentUserServiceMock.Setup(x => x.Role).Returns("Admin");

        // Setup mock for datetime service
        DateTimeServiceMock = new Mock<IDateTime>();
        DateTimeServiceMock.Setup(x => x.UtcNow).Returns(DateTime.UtcNow);

        // Create in-memory database
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        DbContext = new ApplicationDbContext(options, CurrentUserServiceMock.Object);
    }

    /// <summary>
    /// Gets a fresh database context for testing.
    /// </summary>
    protected ApplicationDbContext GetDbContext()
    {
        return DbContext;
    }

    /// <summary>
    /// Creates a new in-memory database context with a unique database name.
    /// </summary>
    protected ApplicationDbContext CreateNewDbContext()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        return new ApplicationDbContext(options, CurrentUserServiceMock.Object);
    }

    /// <summary>
    /// Sets up the current user mock with specific values.
    /// </summary>
    protected void SetupCurrentUser(Guid userId, string email, string role, bool isAuthenticated = true)
    {
        CurrentUserServiceMock.Setup(x => x.UserId).Returns(userId);
        CurrentUserServiceMock.Setup(x => x.Email).Returns(email);
        CurrentUserServiceMock.Setup(x => x.Role).Returns(role);
        CurrentUserServiceMock.Setup(x => x.IsAuthenticated).Returns(isAuthenticated);
    }

    /// <summary>
    /// Sets up the datetime mock with a specific value.
    /// </summary>
    protected void SetupDateTime(DateTime utcNow)
    {
        DateTimeServiceMock.Setup(x => x.UtcNow).Returns(utcNow);
    }

    public void Dispose()
    {
        DbContext.Dispose();
        GC.SuppressFinalize(this);
    }
}

/// <summary>
/// Base class for integration tests.
/// </summary>
public abstract class IntegrationTestBase : TestBase
{
    protected IntegrationTestBase() : base()
    {
    }
}
