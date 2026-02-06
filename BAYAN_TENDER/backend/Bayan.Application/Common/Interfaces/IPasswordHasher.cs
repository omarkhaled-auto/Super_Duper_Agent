namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for password hashing operations.
/// </summary>
public interface IPasswordHasher
{
    /// <summary>
    /// Hashes a password.
    /// </summary>
    /// <param name="password">The plain text password to hash.</param>
    /// <returns>The hashed password.</returns>
    string HashPassword(string password);

    /// <summary>
    /// Verifies a password against a hash.
    /// </summary>
    /// <param name="password">The plain text password to verify.</param>
    /// <param name="passwordHash">The hash to verify against.</param>
    /// <returns>True if the password matches the hash; otherwise, false.</returns>
    bool VerifyPassword(string password, string passwordHash);

    /// <summary>
    /// Generates a random temporary password.
    /// </summary>
    /// <param name="length">The length of the password to generate.</param>
    /// <returns>A random password string.</returns>
    string GenerateTemporaryPassword(int length = 12);
}
