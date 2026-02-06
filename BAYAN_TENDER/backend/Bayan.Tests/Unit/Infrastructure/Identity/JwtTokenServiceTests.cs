using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using Bayan.Infrastructure.Identity;
using FluentAssertions;
using Microsoft.Extensions.Options;

namespace Bayan.Tests.Unit.Infrastructure.Identity;

/// <summary>
/// Unit tests for JwtTokenService.
/// </summary>
public class JwtTokenServiceTests
{
    private readonly JwtSettings _jwtSettings;
    private readonly JwtTokenService _jwtTokenService;

    public JwtTokenServiceTests()
    {
        _jwtSettings = new JwtSettings
        {
            SecretKey = "this-is-a-very-long-secret-key-for-testing-purposes-at-least-32-characters",
            Issuer = "BayanTestIssuer",
            Audience = "BayanTestAudience",
            AccessTokenExpirationMinutes = 60,
            RefreshTokenExpirationDays = 7
        };

        var options = Options.Create(_jwtSettings);
        _jwtTokenService = new JwtTokenService(options);
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_ReturnsValidJwtToken()
    {
        // Arrange
        var user = CreateTestUser();

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        token.Should().NotBeNullOrEmpty();
        token.Should().Contain("."); // JWT tokens have parts separated by dots
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenContainsCorrectUserId()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var user = CreateTestUser(userId);

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        var subClaim = jwtToken.Claims.FirstOrDefault(c => c.Type == JwtRegisteredClaimNames.Sub);
        subClaim.Should().NotBeNull();
        subClaim!.Value.Should().Be(userId.ToString());
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenContainsCorrectEmail()
    {
        // Arrange
        var user = CreateTestUser();
        user.Email = "test@example.com";

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        var emailClaim = jwtToken.Claims.FirstOrDefault(c => c.Type == JwtRegisteredClaimNames.Email);
        emailClaim.Should().NotBeNull();
        emailClaim!.Value.Should().Be("test@example.com");
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenContainsCorrectRole()
    {
        // Arrange
        var user = CreateTestUser();
        user.Role = UserRole.TenderManager;

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        var roleClaim = jwtToken.Claims.FirstOrDefault(c => c.Type == "role");
        roleClaim.Should().NotBeNull();
        roleClaim!.Value.Should().Be("TenderManager");
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenHasCorrectExpiration()
    {
        // Arrange
        var user = CreateTestUser();
        var expectedExpiration = DateTime.UtcNow.AddMinutes(_jwtSettings.AccessTokenExpirationMinutes);

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        jwtToken.ValidTo.Should().BeCloseTo(expectedExpiration, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenHasCorrectIssuer()
    {
        // Arrange
        var user = CreateTestUser();

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        jwtToken.Issuer.Should().Be(_jwtSettings.Issuer);
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenHasCorrectAudience()
    {
        // Arrange
        var user = CreateTestUser();

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        jwtToken.Audiences.Should().Contain(_jwtSettings.Audience);
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenContainsNameIdentifierClaim()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var user = CreateTestUser(userId);

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        var nameIdClaim = jwtToken.Claims.FirstOrDefault(c => c.Type == ClaimTypes.NameIdentifier);
        nameIdClaim.Should().NotBeNull();
        nameIdClaim!.Value.Should().Be(userId.ToString());
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenContainsFullNameClaim()
    {
        // Arrange
        var user = CreateTestUser();
        user.FirstName = "John";
        user.LastName = "Doe";

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        var fullNameClaim = jwtToken.Claims.FirstOrDefault(c => c.Type == "fullName");
        fullNameClaim.Should().NotBeNull();
        fullNameClaim!.Value.Should().Be("John Doe");
    }

    [Fact]
    public void GenerateAccessToken_WithValidUser_TokenContainsJtiClaim()
    {
        // Arrange
        var user = CreateTestUser();

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        var jtiClaim = jwtToken.Claims.FirstOrDefault(c => c.Type == JwtRegisteredClaimNames.Jti);
        jtiClaim.Should().NotBeNull();
        Guid.TryParse(jtiClaim!.Value, out _).Should().BeTrue();
    }

    [Fact]
    public void GenerateRefreshToken_ReturnsNonEmptyString()
    {
        // Act
        var refreshToken = _jwtTokenService.GenerateRefreshToken();

        // Assert
        refreshToken.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void GenerateRefreshToken_ReturnsDifferentTokensOnEachCall()
    {
        // Act
        var token1 = _jwtTokenService.GenerateRefreshToken();
        var token2 = _jwtTokenService.GenerateRefreshToken();
        var token3 = _jwtTokenService.GenerateRefreshToken();

        // Assert
        token1.Should().NotBe(token2);
        token2.Should().NotBe(token3);
        token1.Should().NotBe(token3);
    }

    [Fact]
    public void GenerateRefreshToken_ReturnsUrlSafeToken()
    {
        // Act
        var refreshToken = _jwtTokenService.GenerateRefreshToken();

        // Assert
        refreshToken.Should().NotContain("+");
        refreshToken.Should().NotContain("/");
        refreshToken.Should().NotContain("=");
    }

    [Fact]
    public void GenerateRefreshToken_ReturnsTokenOfSufficientLength()
    {
        // Act
        var refreshToken = _jwtTokenService.GenerateRefreshToken();

        // Assert
        // Base64 of 64 bytes should be around 85-86 characters after URL-safe conversion
        refreshToken.Length.Should().BeGreaterThan(50);
    }

    [Fact]
    public void ValidateAccessToken_WithValidToken_ReturnsUserId()
    {
        // Arrange
        var userId = Guid.NewGuid();
        var user = CreateTestUser(userId);
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Act
        var result = _jwtTokenService.ValidateAccessToken(token);

        // Assert
        result.Should().NotBeNull();
        result.Should().Be(userId);
    }

    [Fact]
    public void ValidateAccessToken_WithInvalidToken_ReturnsNull()
    {
        // Arrange
        var invalidToken = "invalid.jwt.token";

        // Act
        var result = _jwtTokenService.ValidateAccessToken(invalidToken);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public void ValidateAccessToken_WithEmptyToken_ReturnsNull()
    {
        // Act
        var result = _jwtTokenService.ValidateAccessToken(string.Empty);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public void ValidateAccessToken_WithNullToken_ReturnsNull()
    {
        // Act
        var result = _jwtTokenService.ValidateAccessToken(null!);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public void ValidateAccessToken_WithTamperedToken_ReturnsNull()
    {
        // Arrange
        var user = CreateTestUser();
        var token = _jwtTokenService.GenerateAccessToken(user);
        var tamperedToken = token.Substring(0, token.Length - 5) + "xxxxx"; // Tamper with the token

        // Act
        var result = _jwtTokenService.ValidateAccessToken(tamperedToken);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public void ValidateAccessToken_WithTokenFromDifferentIssuer_ReturnsNull()
    {
        // Arrange
        var differentSettings = new JwtSettings
        {
            SecretKey = _jwtSettings.SecretKey,
            Issuer = "DifferentIssuer",
            Audience = _jwtSettings.Audience,
            AccessTokenExpirationMinutes = 60,
            RefreshTokenExpirationDays = 7
        };
        var differentService = new JwtTokenService(Options.Create(differentSettings));
        var user = CreateTestUser();
        var token = differentService.GenerateAccessToken(user);

        // Act
        var result = _jwtTokenService.ValidateAccessToken(token);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public void ValidateAccessToken_WithTokenForDifferentAudience_ReturnsNull()
    {
        // Arrange
        var differentSettings = new JwtSettings
        {
            SecretKey = _jwtSettings.SecretKey,
            Issuer = _jwtSettings.Issuer,
            Audience = "DifferentAudience",
            AccessTokenExpirationMinutes = 60,
            RefreshTokenExpirationDays = 7
        };
        var differentService = new JwtTokenService(Options.Create(differentSettings));
        var user = CreateTestUser();
        var token = differentService.GenerateAccessToken(user);

        // Act
        var result = _jwtTokenService.ValidateAccessToken(token);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public void AccessTokenExpirationMinutes_ReturnsConfiguredValue()
    {
        // Assert
        _jwtTokenService.AccessTokenExpirationMinutes.Should().Be(60);
    }

    [Fact]
    public void RefreshTokenExpirationDays_ReturnsConfiguredValue()
    {
        // Assert
        _jwtTokenService.RefreshTokenExpirationDays.Should().Be(7);
    }

    [Theory]
    [InlineData(UserRole.Admin)]
    [InlineData(UserRole.TenderManager)]
    [InlineData(UserRole.CommercialAnalyst)]
    [InlineData(UserRole.TechnicalPanelist)]
    [InlineData(UserRole.Approver)]
    [InlineData(UserRole.Auditor)]
    [InlineData(UserRole.Bidder)]
    public void GenerateAccessToken_WithDifferentRoles_TokenContainsCorrectRole(UserRole role)
    {
        // Arrange
        var user = CreateTestUser();
        user.Role = role;

        // Act
        var token = _jwtTokenService.GenerateAccessToken(user);

        // Assert
        var handler = new JwtSecurityTokenHandler();
        var jwtToken = handler.ReadJwtToken(token);

        var roleClaim = jwtToken.Claims.FirstOrDefault(c => c.Type == "role");
        roleClaim.Should().NotBeNull();
        roleClaim!.Value.Should().Be(role.ToString());
    }

    private static User CreateTestUser(Guid? userId = null)
    {
        return new User
        {
            Id = userId ?? Guid.NewGuid(),
            Email = "test@example.com",
            PasswordHash = "$2a$12$HashedPassword",
            FirstName = "Test",
            LastName = "User",
            Role = UserRole.Admin,
            IsActive = true,
            EmailVerified = true,
            CreatedAt = DateTime.UtcNow.AddDays(-30)
        };
    }
}
