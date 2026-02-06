namespace Bayan.Application.Common.Models;

/// <summary>
/// Represents the result of an operation.
/// </summary>
public class Result
{
    internal Result(bool succeeded, IEnumerable<string> errors)
    {
        Succeeded = succeeded;
        Errors = errors.ToArray();
    }

    /// <summary>
    /// Indicates whether the operation succeeded.
    /// </summary>
    public bool Succeeded { get; }

    /// <summary>
    /// Gets the errors if the operation failed.
    /// </summary>
    public string[] Errors { get; }

    /// <summary>
    /// Creates a successful result.
    /// </summary>
    public static Result Success()
    {
        return new Result(true, Array.Empty<string>());
    }

    /// <summary>
    /// Creates a failed result with the specified errors.
    /// </summary>
    public static Result Failure(IEnumerable<string> errors)
    {
        return new Result(false, errors);
    }

    /// <summary>
    /// Creates a failed result with a single error.
    /// </summary>
    public static Result Failure(string error)
    {
        return new Result(false, new[] { error });
    }
}

/// <summary>
/// Represents the result of an operation with a value.
/// </summary>
/// <typeparam name="T">The type of the value.</typeparam>
public class Result<T> : Result
{
    internal Result(bool succeeded, T? value, IEnumerable<string> errors)
        : base(succeeded, errors)
    {
        Value = value;
    }

    /// <summary>
    /// Gets the value if the operation succeeded.
    /// </summary>
    public T? Value { get; }

    /// <summary>
    /// Creates a successful result with the specified value.
    /// </summary>
    public static Result<T> Success(T value)
    {
        return new Result<T>(true, value, Array.Empty<string>());
    }

    /// <summary>
    /// Creates a failed result with the specified errors.
    /// </summary>
    public new static Result<T> Failure(IEnumerable<string> errors)
    {
        return new Result<T>(false, default, errors);
    }

    /// <summary>
    /// Creates a failed result with a single error.
    /// </summary>
    public new static Result<T> Failure(string error)
    {
        return new Result<T>(false, default, new[] { error });
    }
}
