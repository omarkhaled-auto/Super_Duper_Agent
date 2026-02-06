using System.Security.Cryptography;
using Bayan.Application.Common.Interfaces;

namespace Bayan.Infrastructure.Identity;

/// <summary>
/// BCrypt-based password hasher implementation.
/// </summary>
public class PasswordHasher : IPasswordHasher
{
    private const int WorkFactor = 12;

    /// <summary>
    /// Hashes a plain text password using BCrypt.
    /// </summary>
    /// <param name="password">The plain text password to hash.</param>
    /// <returns>The BCrypt hashed password.</returns>
    public string HashPassword(string password)
    {
        if (string.IsNullOrEmpty(password))
        {
            throw new ArgumentException("Password cannot be null or empty.", nameof(password));
        }

        return BCrypt.Net.BCrypt.HashPassword(password, WorkFactor);
    }

    /// <summary>
    /// Verifies a plain text password against a BCrypt hash.
    /// </summary>
    /// <param name="password">The plain text password to verify.</param>
    /// <param name="passwordHash">The BCrypt hash to verify against.</param>
    /// <returns>True if the password matches the hash, false otherwise.</returns>
    public bool VerifyPassword(string password, string passwordHash)
    {
        if (string.IsNullOrEmpty(password) || string.IsNullOrEmpty(passwordHash))
        {
            return false;
        }

        try
        {
            return BCrypt.Net.BCrypt.Verify(password, passwordHash);
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Generates a random temporary password.
    /// </summary>
    /// <param name="length">The length of the password to generate.</param>
    /// <returns>A random password string.</returns>
    public string GenerateTemporaryPassword(int length = 12)
    {
        if (length < 8)
        {
            length = 8; // Minimum password length
        }

        const string uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        const string lowercase = "abcdefghijklmnopqrstuvwxyz";
        const string digits = "0123456789";
        const string special = "!@#$%^&*()_+-=";

        var password = new char[length];
        var allChars = uppercase + lowercase + digits + special;

        using var rng = RandomNumberGenerator.Create();

        // Ensure at least one of each required character type
        password[0] = GetRandomChar(rng, uppercase);
        password[1] = GetRandomChar(rng, lowercase);
        password[2] = GetRandomChar(rng, digits);
        password[3] = GetRandomChar(rng, special);

        // Fill the rest with random characters
        for (int i = 4; i < length; i++)
        {
            password[i] = GetRandomChar(rng, allChars);
        }

        // Shuffle the password to randomize position of required characters
        ShuffleArray(rng, password);

        return new string(password);
    }

    private static char GetRandomChar(RandomNumberGenerator rng, string chars)
    {
        var randomBytes = new byte[4];
        rng.GetBytes(randomBytes);
        var randomIndex = Math.Abs(BitConverter.ToInt32(randomBytes, 0)) % chars.Length;
        return chars[randomIndex];
    }

    private static void ShuffleArray(RandomNumberGenerator rng, char[] array)
    {
        var randomBytes = new byte[4];
        for (int i = array.Length - 1; i > 0; i--)
        {
            rng.GetBytes(randomBytes);
            var j = Math.Abs(BitConverter.ToInt32(randomBytes, 0)) % (i + 1);
            (array[i], array[j]) = (array[j], array[i]);
        }
    }
}
