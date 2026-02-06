using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;

namespace Bayan.Tests.Domain;

/// <summary>
/// Unit tests for the User entity.
/// </summary>
public class UserTests
{
    [Fact]
    public void User_FullName_ShouldCombineFirstAndLastName()
    {
        // Arrange
        var user = new User
        {
            FirstName = "John",
            LastName = "Doe"
        };

        // Act
        var fullName = user.FullName;

        // Assert
        fullName.Should().Be("John Doe");
    }

    [Fact]
    public void User_FullName_ShouldTrimWhenOnlyFirstName()
    {
        // Arrange
        var user = new User
        {
            FirstName = "John",
            LastName = ""
        };

        // Act
        var fullName = user.FullName;

        // Assert
        fullName.Should().Be("John");
    }

    [Fact]
    public void User_DefaultValues_ShouldBeCorrect()
    {
        // Arrange & Act
        var user = new User();

        // Assert
        user.IsActive.Should().BeTrue();
        user.EmailVerified.Should().BeFalse();
        user.FailedLoginAttempts.Should().Be(0);
        user.PreferredLanguage.Should().Be("ar");
        user.TimeZone.Should().Be("Asia/Riyadh");
    }

    [Theory]
    [InlineData(UserRole.Admin)]
    [InlineData(UserRole.TenderManager)]
    [InlineData(UserRole.CommercialAnalyst)]
    [InlineData(UserRole.TechnicalPanelist)]
    [InlineData(UserRole.Approver)]
    [InlineData(UserRole.Auditor)]
    [InlineData(UserRole.Bidder)]
    public void User_Role_ShouldAcceptAllValidRoles(UserRole role)
    {
        // Arrange & Act
        var user = new User { Role = role };

        // Assert
        user.Role.Should().Be(role);
    }
}
