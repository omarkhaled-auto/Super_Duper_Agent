using System.Data;

namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for accessing the database connection for Dapper queries.
/// </summary>
public interface IDapperContext
{
    /// <summary>
    /// Creates a new database connection.
    /// </summary>
    /// <returns>An open database connection.</returns>
    IDbConnection CreateConnection();
}
