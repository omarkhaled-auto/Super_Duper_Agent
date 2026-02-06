namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Service for converting between different units of measurement.
/// </summary>
public interface IUomConversionService
{
    /// <summary>
    /// Gets the conversion factor from one UOM to another.
    /// </summary>
    /// <param name="fromUom">Source unit of measurement.</param>
    /// <param name="toUom">Target unit of measurement.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The conversion factor, or null if conversion is not possible.</returns>
    Task<decimal?> GetConversionFactorAsync(string fromUom, string toUom, CancellationToken cancellationToken = default);

    /// <summary>
    /// Determines if conversion is possible between two UOMs.
    /// </summary>
    /// <param name="fromUom">Source unit of measurement.</param>
    /// <param name="toUom">Target unit of measurement.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>True if conversion is possible, false otherwise.</returns>
    Task<bool> CanConvertAsync(string fromUom, string toUom, CancellationToken cancellationToken = default);

    /// <summary>
    /// Converts a value from one UOM to another.
    /// </summary>
    /// <param name="value">The value to convert.</param>
    /// <param name="fromUom">Source unit of measurement.</param>
    /// <param name="toUom">Target unit of measurement.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The converted value, or null if conversion is not possible.</returns>
    Task<decimal?> ConvertAsync(decimal value, string fromUom, string toUom, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the reason why two UOMs cannot be converted.
    /// </summary>
    /// <param name="fromUom">Source unit of measurement.</param>
    /// <param name="toUom">Target unit of measurement.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Reason for non-convertibility, or null if conversion is possible.</returns>
    Task<string?> GetNonConvertibleReasonAsync(string fromUom, string toUom, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the category for a given UOM.
    /// </summary>
    /// <param name="uomCode">UOM code.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The category name, or null if UOM is not found.</returns>
    Task<string?> GetUomCategoryAsync(string uomCode, CancellationToken cancellationToken = default);
}
