namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for fuzzy string matching operations.
/// </summary>
public interface IFuzzyMatchingService
{
    /// <summary>
    /// Calculates the similarity between two strings.
    /// </summary>
    /// <param name="string1">First string to compare.</param>
    /// <param name="string2">Second string to compare.</param>
    /// <returns>Similarity score between 0 and 100.</returns>
    double CalculateSimilarity(string? string1, string? string2);

    /// <summary>
    /// Finds the best match for a search term from a list of candidates.
    /// </summary>
    /// <param name="searchTerm">The term to search for.</param>
    /// <param name="candidates">List of candidate strings to match against.</param>
    /// <returns>Tuple containing the best match and its confidence score (0-100).</returns>
    (string? BestMatch, double Confidence) FindBestMatch(string? searchTerm, IEnumerable<string> candidates);

    /// <summary>
    /// Finds the best match for a search term from a list of candidates with custom keys.
    /// </summary>
    /// <typeparam name="T">Type of the candidate objects.</typeparam>
    /// <param name="searchTerm">The term to search for.</param>
    /// <param name="candidates">List of candidate objects.</param>
    /// <param name="keySelector">Function to extract the string to match against from each candidate.</param>
    /// <returns>Tuple containing the best matching object and its confidence score (0-100).</returns>
    (T? BestMatch, double Confidence) FindBestMatch<T>(
        string? searchTerm,
        IEnumerable<T> candidates,
        Func<T, string?> keySelector) where T : class;

    /// <summary>
    /// Finds all matches above a confidence threshold.
    /// </summary>
    /// <param name="searchTerm">The term to search for.</param>
    /// <param name="candidates">List of candidate strings.</param>
    /// <param name="minConfidence">Minimum confidence threshold (0-100).</param>
    /// <returns>List of matches with their confidence scores, ordered by confidence descending.</returns>
    IEnumerable<(string Match, double Confidence)> FindMatches(
        string? searchTerm,
        IEnumerable<string> candidates,
        double minConfidence = 0);

    /// <summary>
    /// Finds all matches above a confidence threshold with custom keys.
    /// </summary>
    /// <typeparam name="T">Type of the candidate objects.</typeparam>
    /// <param name="searchTerm">The term to search for.</param>
    /// <param name="candidates">List of candidate objects.</param>
    /// <param name="keySelector">Function to extract the string to match against from each candidate.</param>
    /// <param name="minConfidence">Minimum confidence threshold (0-100).</param>
    /// <returns>List of matching objects with their confidence scores, ordered by confidence descending.</returns>
    IEnumerable<(T Match, double Confidence)> FindMatches<T>(
        string? searchTerm,
        IEnumerable<T> candidates,
        Func<T, string?> keySelector,
        double minConfidence = 0) where T : class;

    /// <summary>
    /// Calculates token set ratio similarity (better for descriptions with similar words in different order).
    /// </summary>
    /// <param name="string1">First string to compare.</param>
    /// <param name="string2">Second string to compare.</param>
    /// <returns>Token set ratio similarity score between 0 and 100.</returns>
    double CalculateTokenSetRatio(string? string1, string? string2);

    /// <summary>
    /// Calculates partial ratio similarity (better for finding substrings).
    /// </summary>
    /// <param name="string1">First string to compare.</param>
    /// <param name="string2">Second string to compare.</param>
    /// <returns>Partial ratio similarity score between 0 and 100.</returns>
    double CalculatePartialRatio(string? string1, string? string2);
}
