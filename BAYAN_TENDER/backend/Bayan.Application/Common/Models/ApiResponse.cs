using System.Text.Json.Serialization;

namespace Bayan.Application.Common.Models;

/// <summary>
/// Standard API response wrapper.
/// </summary>
/// <typeparam name="T">The type of data returned.</typeparam>
public class ApiResponse<T>
{
    /// <summary>
    /// Indicates whether the request was successful.
    /// </summary>
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    /// <summary>
    /// The response data.
    /// </summary>
    [JsonPropertyName("data")]
    public T? Data { get; set; }

    /// <summary>
    /// The response message.
    /// </summary>
    [JsonPropertyName("message")]
    public string? Message { get; set; }

    /// <summary>
    /// Error details if the request failed.
    /// </summary>
    [JsonPropertyName("errors")]
    public IEnumerable<string>? Errors { get; set; }

    /// <summary>
    /// Timestamp of the response.
    /// </summary>
    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;

    /// <summary>
    /// Creates a successful response with data.
    /// </summary>
    public static ApiResponse<T> SuccessResponse(T data, string? message = null)
    {
        return new ApiResponse<T>
        {
            Success = true,
            Data = data,
            Message = message
        };
    }

    /// <summary>
    /// Creates a failed response with errors.
    /// </summary>
    public static ApiResponse<T> FailureResponse(string message, IEnumerable<string>? errors = null)
    {
        return new ApiResponse<T>
        {
            Success = false,
            Message = message,
            Errors = errors
        };
    }

    /// <summary>
    /// Creates a failed response with a single error.
    /// </summary>
    public static ApiResponse<T> FailureResponse(string message, string error)
    {
        return new ApiResponse<T>
        {
            Success = false,
            Message = message,
            Errors = new[] { error }
        };
    }
}

/// <summary>
/// Non-generic API response for operations without data.
/// </summary>
public class ApiResponse : ApiResponse<object>
{
    /// <summary>
    /// Creates a successful response without data.
    /// </summary>
    public static ApiResponse SuccessResponse(string? message = null)
    {
        return new ApiResponse
        {
            Success = true,
            Message = message
        };
    }

    /// <summary>
    /// Creates a failed response.
    /// </summary>
    public new static ApiResponse FailureResponse(string message, IEnumerable<string>? errors = null)
    {
        return new ApiResponse
        {
            Success = false,
            Message = message,
            Errors = errors
        };
    }
}
