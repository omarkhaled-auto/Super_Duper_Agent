using System.Data;
using Bayan.Application.Common.Interfaces;
using Microsoft.Extensions.Configuration;
using Npgsql;

namespace Bayan.Infrastructure.Data;

/// <summary>
/// Dapper context for raw SQL queries.
/// </summary>
public class DapperContext : IDapperContext
{
    private readonly string _connectionString;

    public DapperContext(IConfiguration configuration)
    {
        _connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");
    }

    /// <inheritdoc />
    public IDbConnection CreateConnection()
    {
        return new NpgsqlConnection(_connectionString);
    }
}
