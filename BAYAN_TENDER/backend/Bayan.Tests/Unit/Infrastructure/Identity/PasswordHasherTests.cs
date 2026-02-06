using Bayan.Infrastructure.Identity;
using FluentAssertions;

namespace Bayan.Tests.Unit.Infrastructure.Identity;

/// <summary>
/// Unit tests for PasswordHasher.
/// </summary>
public class PasswordHasherTests
{
    private readonly PasswordHasher _passwordHasher;

    public PasswordHasherTests()
    {
        _passwordHasher = new PasswordHasher();
    }

    [Fact]
    public void HashPassword_WithValidPassword_ReturnsHashedPassword()
    {
        // Arrange
        var password = "MySecurePassword123!";

        // Act
        var hash = _passwordHasher.HashPassword(password);

        // Assert
        hash.Should().NotBeNullOrEmpty();
        hash.Should().NotBe(password);
    }

    [Fact]
    public void HashPassword_WithSamePassword_ProducesDifferentHashes()
    {
        // Arrange
        var password = "MySecurePassword123!";

        // Act
        var hash1 = _passwordHasher.HashPassword(password);
        var hash2 = _passwordHasher.HashPassword(password);

        // Assert
        hash1.Should().NotBe(hash2);
    }

    [Fact]
    public void HashPassword_WithNullPassword_ThrowsArgumentException()
    {
        // Act
        var act = () => _passwordHasher.HashPassword(null!);

        // Assert
        act.Should().Throw<ArgumentException>()
            .WithMessage("Password cannot be null or empty.*");
    }

    [Fact]
    public void HashPassword_WithEmptyPassword_ThrowsArgumentException()
    {
        // Act
        var act = () => _passwordHasher.HashPassword(string.Empty);

        // Assert
        act.Should().Throw<ArgumentException>()
            .WithMessage("Password cannot be null or empty.*");
    }

    [Fact]
    public void HashPassword_ReturnsHashInBCryptFormat()
    {
        // Arrange
        var password = "TestPassword123!";

        // Act
        var hash = _passwordHasher.HashPassword(password);

        // Assert
        // BCrypt hashes start with $2a$, $2b$, or $2y$ and contain the version and work factor
        hash.Should().StartWith("$2");
        hash.Should().Contain("$12$"); // Work factor of 12
    }

    [Fact]
    public void VerifyPassword_WithCorrectPassword_ReturnsTrue()
    {
        // Arrange
        var password = "MySecurePassword123!";
        var hash = _passwordHasher.HashPassword(password);

        // Act
        var result = _passwordHasher.VerifyPassword(password, hash);

        // Assert
        result.Should().BeTrue();
    }

    [Fact]
    public void VerifyPassword_WithIncorrectPassword_ReturnsFalse()
    {
        // Arrange
        var password = "MySecurePassword123!";
        var wrongPassword = "WrongPassword123!";
        var hash = _passwordHasher.HashPassword(password);

        // Act
        var result = _passwordHasher.VerifyPassword(wrongPassword, hash);

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public void VerifyPassword_WithNullPassword_ReturnsFalse()
    {
        // Arrange
        var hash = "$2a$12$validHashValue";

        // Act
        var result = _passwordHasher.VerifyPassword(null!, hash);

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public void VerifyPassword_WithEmptyPassword_ReturnsFalse()
    {
        // Arrange
        var hash = "$2a$12$validHashValue";

        // Act
        var result = _passwordHasher.VerifyPassword(string.Empty, hash);

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public void VerifyPassword_WithNullHash_ReturnsFalse()
    {
        // Arrange
        var password = "MySecurePassword123!";

        // Act
        var result = _passwordHasher.VerifyPassword(password, null!);

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public void VerifyPassword_WithEmptyHash_ReturnsFalse()
    {
        // Arrange
        var password = "MySecurePassword123!";

        // Act
        var result = _passwordHasher.VerifyPassword(password, string.Empty);

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public void VerifyPassword_WithInvalidHash_ReturnsFalse()
    {
        // Arrange
        var password = "MySecurePassword123!";
        var invalidHash = "not-a-valid-bcrypt-hash";

        // Act
        var result = _passwordHasher.VerifyPassword(password, invalidHash);

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public void VerifyPassword_WithSimilarPasswords_DistinguishesThem()
    {
        // Arrange
        var password1 = "Password123";
        var password2 = "Password124"; // One character different
        var hash = _passwordHasher.HashPassword(password1);

        // Act
        var result1 = _passwordHasher.VerifyPassword(password1, hash);
        var result2 = _passwordHasher.VerifyPassword(password2, hash);

        // Assert
        result1.Should().BeTrue();
        result2.Should().BeFalse();
    }

    [Fact]
    public void VerifyPassword_WithCaseSensitivePasswords_DistinguishesThem()
    {
        // Arrange
        var password = "Password123";
        var passwordDifferentCase = "password123";
        var hash = _passwordHasher.HashPassword(password);

        // Act
        var result1 = _passwordHasher.VerifyPassword(password, hash);
        var result2 = _passwordHasher.VerifyPassword(passwordDifferentCase, hash);

        // Assert
        result1.Should().BeTrue();
        result2.Should().BeFalse();
    }

    [Fact]
    public void GenerateTemporaryPassword_ReturnsPasswordOfDefaultLength()
    {
        // Act
        var password = _passwordHasher.GenerateTemporaryPassword();

        // Assert
        password.Should().HaveLength(12); // Default length
    }

    [Fact]
    public void GenerateTemporaryPassword_WithCustomLength_ReturnsPasswordOfSpecifiedLength()
    {
        // Arrange
        var length = 16;

        // Act
        var password = _passwordHasher.GenerateTemporaryPassword(length);

        // Assert
        password.Should().HaveLength(length);
    }

    [Fact]
    public void GenerateTemporaryPassword_WithLengthLessThanMinimum_ReturnsMinimumLength()
    {
        // Arrange
        var length = 5; // Less than minimum (8)

        // Act
        var password = _passwordHasher.GenerateTemporaryPassword(length);

        // Assert
        password.Should().HaveLength(8); // Should be minimum length
    }

    [Fact]
    public void GenerateTemporaryPassword_ContainsUppercaseCharacter()
    {
        // Act
        var password = _passwordHasher.GenerateTemporaryPassword();

        // Assert
        password.Should().MatchRegex("[A-Z]");
    }

    [Fact]
    public void GenerateTemporaryPassword_ContainsLowercaseCharacter()
    {
        // Act
        var password = _passwordHasher.GenerateTemporaryPassword();

        // Assert
        password.Should().MatchRegex("[a-z]");
    }

    [Fact]
    public void GenerateTemporaryPassword_ContainsDigit()
    {
        // Act
        var password = _passwordHasher.GenerateTemporaryPassword();

        // Assert
        password.Should().MatchRegex("[0-9]");
    }

    [Fact]
    public void GenerateTemporaryPassword_ContainsSpecialCharacter()
    {
        // Act
        var password = _passwordHasher.GenerateTemporaryPassword();

        // Assert
        password.Should().MatchRegex(@"[!@#$%^&*()_+\-=]");
    }

    [Fact]
    public void GenerateTemporaryPassword_GeneratesUniquePasswords()
    {
        // Act
        var passwords = new HashSet<string>();
        for (int i = 0; i < 100; i++)
        {
            passwords.Add(_passwordHasher.GenerateTemporaryPassword());
        }

        // Assert
        passwords.Should().HaveCount(100); // All passwords should be unique
    }

    [Fact]
    public void GenerateTemporaryPassword_CanBeHashedAndVerified()
    {
        // Act
        var password = _passwordHasher.GenerateTemporaryPassword();
        var hash = _passwordHasher.HashPassword(password);
        var verificationResult = _passwordHasher.VerifyPassword(password, hash);

        // Assert
        verificationResult.Should().BeTrue();
    }

    [Theory]
    [InlineData(8)]
    [InlineData(12)]
    [InlineData(16)]
    [InlineData(20)]
    [InlineData(32)]
    public void GenerateTemporaryPassword_WithVariousLengths_ReturnsCorrectLength(int length)
    {
        // Act
        var password = _passwordHasher.GenerateTemporaryPassword(length);

        // Assert
        password.Should().HaveLength(length);
    }

    [Fact]
    public void VerifyPassword_WithPasswordContainingSpecialCharacters_WorksCorrectly()
    {
        // Arrange
        var password = "P@ssw0rd!#$%^&*()";
        var hash = _passwordHasher.HashPassword(password);

        // Act
        var result = _passwordHasher.VerifyPassword(password, hash);

        // Assert
        result.Should().BeTrue();
    }

    [Fact]
    public void VerifyPassword_WithPasswordContainingUnicode_WorksCorrectly()
    {
        // Arrange
        var password = "Password123";
        var hash = _passwordHasher.HashPassword(password);

        // Act
        var result = _passwordHasher.VerifyPassword(password, hash);

        // Assert
        result.Should().BeTrue();
    }

    [Fact]
    public void HashPassword_WithLongPassword_WorksCorrectly()
    {
        // Arrange
        var password = new string('a', 100); // Long password

        // Act
        var hash = _passwordHasher.HashPassword(password);
        var result = _passwordHasher.VerifyPassword(password, hash);

        // Assert
        hash.Should().NotBeNullOrEmpty();
        result.Should().BeTrue();
    }

    [Fact]
    public void VerifyPassword_WithWhitespacePassword_HandlesCorrectly()
    {
        // Arrange
        var password = "   Password   "; // Password with whitespace
        var hash = _passwordHasher.HashPassword(password);

        // Act
        var resultWithSameWhitespace = _passwordHasher.VerifyPassword(password, hash);
        var resultWithoutWhitespace = _passwordHasher.VerifyPassword("Password", hash);

        // Assert
        resultWithSameWhitespace.Should().BeTrue();
        resultWithoutWhitespace.Should().BeFalse();
    }
}
