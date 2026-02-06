using Bayan.Application.Common.Interfaces;
using FuzzySharp;
using FuzzySharp.PreProcess;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Matching;

/// <summary>
/// Implementation of fuzzy string matching using FuzzySharp library.
/// </summary>
public class FuzzyMatchingService : IFuzzyMatchingService
{
    private readonly ILogger<FuzzyMatchingService> _logger;

    /// <summary>
    /// Default threshold for auto-matching (80%).
    /// </summary>
    public const double DefaultAutoMatchThreshold = 80.0;

    public FuzzyMatchingService(ILogger<FuzzyMatchingService> logger)
    {
        _logger = logger;
    }

    /// <inheritdoc />
    public double CalculateSimilarity(string? string1, string? string2)
    {
        if (string.IsNullOrWhiteSpace(string1) || string.IsNullOrWhiteSpace(string2))
        {
            return 0;
        }

        try
        {
            // Use weighted ratio which combines multiple algorithms for best results
            return Fuzz.WeightedRatio(
                string1.Trim(),
                string2.Trim(),
                PreprocessMode.Full);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error calculating similarity between '{String1}' and '{String2}'", string1, string2);
            return 0;
        }
    }

    /// <inheritdoc />
    public (string? BestMatch, double Confidence) FindBestMatch(string? searchTerm, IEnumerable<string> candidates)
    {
        if (string.IsNullOrWhiteSpace(searchTerm) || candidates == null)
        {
            return (null, 0);
        }

        var candidateList = candidates.Where(c => !string.IsNullOrWhiteSpace(c)).ToList();
        if (candidateList.Count == 0)
        {
            return (null, 0);
        }

        try
        {
            var result = Process.ExtractOne(
                searchTerm.Trim(),
                candidateList);

            return result != null ? (result.Value, result.Score) : (null, 0);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error finding best match for '{SearchTerm}'", searchTerm);
            return (null, 0);
        }
    }

    /// <inheritdoc />
    public (T? BestMatch, double Confidence) FindBestMatch<T>(
        string? searchTerm,
        IEnumerable<T> candidates,
        Func<T, string?> keySelector) where T : class
    {
        if (string.IsNullOrWhiteSpace(searchTerm) || candidates == null)
        {
            return (null, 0);
        }

        var candidateList = candidates.ToList();
        if (candidateList.Count == 0)
        {
            return (null, 0);
        }

        try
        {
            // Build a dictionary mapping keys to candidates
            var keyToCandidates = candidateList
                .Select(c => new { Candidate = c, Key = keySelector(c) })
                .Where(x => !string.IsNullOrWhiteSpace(x.Key))
                .ToList();

            if (keyToCandidates.Count == 0)
            {
                return (null, 0);
            }

            var keys = keyToCandidates.Select(x => x.Key!).ToList();
            var result = Process.ExtractOne(
                searchTerm.Trim(),
                keys);

            if (result == null)
            {
                return (null, 0);
            }

            var match = keyToCandidates.FirstOrDefault(x => x.Key == result.Value);
            return match != null ? (match.Candidate, result.Score) : (null, 0);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error finding best match for '{SearchTerm}'", searchTerm);
            return (null, 0);
        }
    }

    /// <inheritdoc />
    public IEnumerable<(string Match, double Confidence)> FindMatches(
        string? searchTerm,
        IEnumerable<string> candidates,
        double minConfidence = 0)
    {
        if (string.IsNullOrWhiteSpace(searchTerm) || candidates == null)
        {
            return Enumerable.Empty<(string, double)>();
        }

        var candidateList = candidates.Where(c => !string.IsNullOrWhiteSpace(c)).ToList();
        if (candidateList.Count == 0)
        {
            return Enumerable.Empty<(string, double)>();
        }

        try
        {
            var results = Process.ExtractAll(
                searchTerm.Trim(),
                candidateList,
                cutoff: (int)minConfidence);

            return results
                .OrderByDescending(r => r.Score)
                .Select(r => (r.Value, (double)r.Score));
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error finding matches for '{SearchTerm}'", searchTerm);
            return Enumerable.Empty<(string, double)>();
        }
    }

    /// <inheritdoc />
    public IEnumerable<(T Match, double Confidence)> FindMatches<T>(
        string? searchTerm,
        IEnumerable<T> candidates,
        Func<T, string?> keySelector,
        double minConfidence = 0) where T : class
    {
        if (string.IsNullOrWhiteSpace(searchTerm) || candidates == null)
        {
            return Enumerable.Empty<(T, double)>();
        }

        var candidateList = candidates.ToList();
        if (candidateList.Count == 0)
        {
            return Enumerable.Empty<(T, double)>();
        }

        try
        {
            var keyToCandidates = candidateList
                .Select(c => new { Candidate = c, Key = keySelector(c) })
                .Where(x => !string.IsNullOrWhiteSpace(x.Key))
                .ToList();

            if (keyToCandidates.Count == 0)
            {
                return Enumerable.Empty<(T, double)>();
            }

            var keys = keyToCandidates.Select(x => x.Key!).ToList();
            var results = Process.ExtractAll(
                searchTerm.Trim(),
                keys,
                cutoff: (int)minConfidence);

            return results
                .OrderByDescending(r => r.Score)
                .Select(r =>
                {
                    var match = keyToCandidates.First(x => x.Key == r.Value);
                    return (match.Candidate, (double)r.Score);
                });
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error finding matches for '{SearchTerm}'", searchTerm);
            return Enumerable.Empty<(T, double)>();
        }
    }

    /// <inheritdoc />
    public double CalculateTokenSetRatio(string? string1, string? string2)
    {
        if (string.IsNullOrWhiteSpace(string1) || string.IsNullOrWhiteSpace(string2))
        {
            return 0;
        }

        try
        {
            // Token set ratio is best for descriptions where words may be in different order
            return Fuzz.TokenSetRatio(
                string1.Trim(),
                string2.Trim(),
                PreprocessMode.Full);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error calculating token set ratio between '{String1}' and '{String2}'", string1, string2);
            return 0;
        }
    }

    /// <inheritdoc />
    public double CalculatePartialRatio(string? string1, string? string2)
    {
        if (string.IsNullOrWhiteSpace(string1) || string.IsNullOrWhiteSpace(string2))
        {
            return 0;
        }

        try
        {
            // Partial ratio is best for finding substrings
            return Fuzz.PartialRatio(
                string1.Trim(),
                string2.Trim(),
                PreprocessMode.Full);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error calculating partial ratio between '{String1}' and '{String2}'", string1, string2);
            return 0;
        }
    }
}
