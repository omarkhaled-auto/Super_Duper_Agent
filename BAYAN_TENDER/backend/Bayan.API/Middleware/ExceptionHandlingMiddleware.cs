using System.Net;
using System.Text.Json;
using FluentValidation;

namespace Bayan.API.Middleware;

/// <summary>
/// Middleware for handling exceptions globally and returning consistent error responses.
/// </summary>
public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(RequestDelegate next, ILogger<ExceptionHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            await HandleExceptionAsync(context, ex);
        }
    }

    private async Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        var response = context.Response;
        response.ContentType = "application/json";

        var errorResponse = new ErrorResponse();

        switch (exception)
        {
            case ValidationException validationException:
                response.StatusCode = (int)HttpStatusCode.BadRequest;
                errorResponse.Message = "Validation failed";
                errorResponse.Errors = validationException.Errors
                    .Select(e => new ValidationError
                    {
                        Property = e.PropertyName,
                        Message = e.ErrorMessage
                    })
                    .ToList();
                _logger.LogWarning("Validation exception: {Errors}",
                    string.Join(", ", validationException.Errors.Select(e => e.ErrorMessage)));
                break;

            case UnauthorizedAccessException:
                response.StatusCode = (int)HttpStatusCode.Unauthorized;
                errorResponse.Message = exception.Message;
                _logger.LogWarning("Unauthorized access: {Message}", exception.Message);
                break;

            case KeyNotFoundException:
                response.StatusCode = (int)HttpStatusCode.NotFound;
                errorResponse.Message = exception.Message;
                _logger.LogWarning("Resource not found: {Message}", exception.Message);
                break;

            case ArgumentException:
                response.StatusCode = (int)HttpStatusCode.BadRequest;
                errorResponse.Message = exception.Message;
                _logger.LogWarning("Invalid argument: {Message}", exception.Message);
                break;

            case InvalidOperationException:
                response.StatusCode = (int)HttpStatusCode.BadRequest;
                errorResponse.Message = exception.Message;
                _logger.LogWarning("Invalid operation: {Message}", exception.Message);
                break;

            default:
                response.StatusCode = (int)HttpStatusCode.InternalServerError;
                errorResponse.Message = "An unexpected error occurred. Please try again later.";
                _logger.LogError(exception, "Unhandled exception occurred");
                break;
        }

        errorResponse.StatusCode = response.StatusCode;
        errorResponse.Timestamp = DateTime.UtcNow;

        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };

        await response.WriteAsync(JsonSerializer.Serialize(errorResponse, options));
    }
}

/// <summary>
/// Standardized error response model.
/// </summary>
public class ErrorResponse
{
    /// <summary>
    /// HTTP status code.
    /// </summary>
    public int StatusCode { get; set; }

    /// <summary>
    /// Error message.
    /// </summary>
    public string Message { get; set; } = string.Empty;

    /// <summary>
    /// Validation errors (if applicable).
    /// </summary>
    public List<ValidationError>? Errors { get; set; }

    /// <summary>
    /// Timestamp of the error.
    /// </summary>
    public DateTime Timestamp { get; set; }
}

/// <summary>
/// Validation error details.
/// </summary>
public class ValidationError
{
    /// <summary>
    /// Property that failed validation.
    /// </summary>
    public string Property { get; set; } = string.Empty;

    /// <summary>
    /// Validation error message.
    /// </summary>
    public string Message { get; set; } = string.Empty;
}

/// <summary>
/// Extension methods for exception handling middleware.
/// </summary>
public static class ExceptionHandlingMiddlewareExtensions
{
    /// <summary>
    /// Adds the exception handling middleware to the application pipeline.
    /// </summary>
    public static IApplicationBuilder UseExceptionHandling(this IApplicationBuilder app)
    {
        return app.UseMiddleware<ExceptionHandlingMiddleware>();
    }
}
