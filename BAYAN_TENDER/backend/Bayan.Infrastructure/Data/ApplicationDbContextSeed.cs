using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using Bayan.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Data;

/// <summary>
/// Seeds the database with initial data including UOMs, system settings, and demo users.
/// </summary>
public class ApplicationDbContextSeed
{
    private readonly ApplicationDbContext _context;
    private readonly ILogger<ApplicationDbContextSeed> _logger;

    // Default password for demo users: Bayan@2024
    // BCrypt hash generated with work factor 12
    private const string DefaultPasswordHash = "$2a$12$5hpH3Ub2qoomrv7AKSWM9el09hhaxLCjZ3/CYZ0QmdyJ.xoc.wD8a";

    public ApplicationDbContextSeed(
        ApplicationDbContext context,
        ILogger<ApplicationDbContextSeed> logger)
    {
        _context = context;
        _logger = logger;
    }

    /// <summary>
    /// Seeds all initial data into the database.
    /// </summary>
    public async Task SeedAllAsync()
    {
        try
        {
            await SeedUnitsOfMeasureAsync();
            await SeedSystemSettingsAsync();
            await SeedDemoUsersAsync();
            await SeedDemoBiddersAsync();

            _logger.LogInformation("Database seeding completed successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred while seeding the database");
            throw;
        }
    }

    /// <summary>
    /// Seeds the 16 standard units of measure as specified in the PRD.
    /// </summary>
    private async Task SeedUnitsOfMeasureAsync()
    {
        if (await _context.UnitsOfMeasure.AnyAsync())
        {
            _logger.LogInformation("Units of measure already seeded, skipping...");
            return;
        }

        _logger.LogInformation("Seeding units of measure...");

        var unitsOfMeasure = new List<UnitOfMeasure>
        {
            // Area measurements
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "m2",
                Name = "Square Meter",
                Category = "Area",
                Description = "Standard metric unit for area measurement",
                ConversionFactor = 1.0m,
                BaseUnitCode = null, // Base unit for Area
                IsActive = true,
                DisplayOrder = 1,
                CreatedAt = DateTime.UtcNow
            },
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "sqft",
                Name = "Square Foot",
                Category = "Area",
                Description = "Imperial unit for area measurement",
                ConversionFactor = 0.092903m, // 1 sqft = 0.092903 m2
                BaseUnitCode = "m2",
                IsActive = true,
                DisplayOrder = 2,
                CreatedAt = DateTime.UtcNow
            },

            // Length measurements
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "lm",
                Name = "Linear Meter",
                Category = "Length",
                Description = "Linear meter for length measurement",
                ConversionFactor = 1.0m,
                BaseUnitCode = null, // Base unit for Length
                IsActive = true,
                DisplayOrder = 3,
                CreatedAt = DateTime.UtcNow
            },
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "m",
                Name = "Meter",
                Category = "Length",
                Description = "Standard metric unit for length",
                ConversionFactor = 1.0m,
                BaseUnitCode = "lm",
                IsActive = true,
                DisplayOrder = 4,
                CreatedAt = DateTime.UtcNow
            },

            // Count/Quantity
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "nos",
                Name = "Numbers",
                Category = "Count",
                Description = "Count of individual items",
                ConversionFactor = 1.0m,
                BaseUnitCode = null, // Base unit for Count
                IsActive = true,
                DisplayOrder = 5,
                CreatedAt = DateTime.UtcNow
            },

            // Weight measurements
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "kg",
                Name = "Kilogram",
                Category = "Weight",
                Description = "Standard metric unit for weight",
                ConversionFactor = 1.0m,
                BaseUnitCode = null, // Base unit for Weight
                IsActive = true,
                DisplayOrder = 6,
                CreatedAt = DateTime.UtcNow
            },
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "ton",
                Name = "Metric Ton",
                Category = "Weight",
                Description = "1000 kilograms",
                ConversionFactor = 1000.0m, // 1 ton = 1000 kg
                BaseUnitCode = "kg",
                IsActive = true,
                DisplayOrder = 7,
                CreatedAt = DateTime.UtcNow
            },

            // Volume measurements
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "ltr",
                Name = "Liter",
                Category = "Volume",
                Description = "Standard metric unit for liquid volume",
                ConversionFactor = 0.001m, // 1 ltr = 0.001 m3
                BaseUnitCode = "m3",
                IsActive = true,
                DisplayOrder = 8,
                CreatedAt = DateTime.UtcNow
            },
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "m3",
                Name = "Cubic Meter",
                Category = "Volume",
                Description = "Standard metric unit for volume",
                ConversionFactor = 1.0m,
                BaseUnitCode = null, // Base unit for Volume
                IsActive = true,
                DisplayOrder = 9,
                CreatedAt = DateTime.UtcNow
            },

            // Lump/Bulk items
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "set",
                Name = "Set",
                Category = "Lump",
                Description = "A complete set of items",
                ConversionFactor = 1.0m,
                BaseUnitCode = null,
                IsActive = true,
                DisplayOrder = 10,
                CreatedAt = DateTime.UtcNow
            },
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "lot",
                Name = "Lot",
                Category = "Lump",
                Description = "A lot or batch of items",
                ConversionFactor = 1.0m,
                BaseUnitCode = null,
                IsActive = true,
                DisplayOrder = 11,
                CreatedAt = DateTime.UtcNow
            },

            // Time-based measurements
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "day",
                Name = "Day",
                Category = "Time",
                Description = "One calendar day",
                ConversionFactor = 1.0m,
                BaseUnitCode = null, // Base unit for Time
                IsActive = true,
                DisplayOrder = 12,
                CreatedAt = DateTime.UtcNow
            },
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "week",
                Name = "Week",
                Category = "Time",
                Description = "One calendar week (7 days)",
                ConversionFactor = 7.0m, // 1 week = 7 days
                BaseUnitCode = "day",
                IsActive = true,
                DisplayOrder = 13,
                CreatedAt = DateTime.UtcNow
            },
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "month",
                Name = "Month",
                Category = "Time",
                Description = "One calendar month",
                ConversionFactor = 30.0m, // Approximate: 1 month = 30 days
                BaseUnitCode = "day",
                IsActive = true,
                DisplayOrder = 14,
                CreatedAt = DateTime.UtcNow
            },

            // Special measurements
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "LS",
                Name = "Lump Sum",
                Category = "Lump",
                Description = "A fixed total price for a scope of work",
                ConversionFactor = 1.0m,
                BaseUnitCode = null,
                IsActive = true,
                DisplayOrder = 15,
                CreatedAt = DateTime.UtcNow
            },
            new UnitOfMeasure
            {
                Id = Guid.NewGuid(),
                Code = "%",
                Name = "Percentage",
                Category = "Percentage",
                Description = "Percentage of a base value",
                ConversionFactor = 1.0m,
                BaseUnitCode = null,
                IsActive = true,
                DisplayOrder = 16,
                CreatedAt = DateTime.UtcNow
            }
        };

        await _context.UnitsOfMeasure.AddRangeAsync(unitsOfMeasure);
        await _context.SaveChangesAsync();

        _logger.LogInformation("Seeded {Count} units of measure", unitsOfMeasure.Count);
    }

    /// <summary>
    /// Seeds system settings with default values.
    /// </summary>
    private async Task SeedSystemSettingsAsync()
    {
        if (await _context.SystemSettings.AnyAsync())
        {
            _logger.LogInformation("System settings already seeded, skipping...");
            return;
        }

        _logger.LogInformation("Seeding system settings...");

        var systemSettings = new List<SystemSetting>
        {
            // Currency settings
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "default_currency",
                Value = "AED",
                DataType = "string",
                Description = "Default currency for tender amounts",
                Category = "Finance",
                IsEditable = true,
                DisplayOrder = 1,
                CreatedAt = DateTime.UtcNow
            },

            // Bid settings
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "default_bid_validity_days",
                Value = "90",
                DataType = "int",
                Description = "Default number of days a bid remains valid",
                Category = "Bidding",
                IsEditable = true,
                DisplayOrder = 2,
                CreatedAt = DateTime.UtcNow
            },
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "clarification_buffer_days",
                Value = "3",
                DataType = "int",
                Description = "Minimum days before submission deadline for clarification cutoff",
                Category = "Bidding",
                IsEditable = true,
                DisplayOrder = 3,
                CreatedAt = DateTime.UtcNow
            },

            // Security settings
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "session_timeout_minutes",
                Value = "60",
                DataType = "int",
                Description = "User session timeout in minutes",
                Category = "Security",
                IsEditable = true,
                DisplayOrder = 4,
                CreatedAt = DateTime.UtcNow
            },
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "password_min_length",
                Value = "8",
                DataType = "int",
                Description = "Minimum password length for user accounts",
                Category = "Security",
                IsEditable = true,
                DisplayOrder = 5,
                CreatedAt = DateTime.UtcNow
            },

            // Localization settings
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "default_language",
                Value = "en",
                DataType = "string",
                Description = "Default system language (en, ar)",
                Category = "Localization",
                IsEditable = true,
                DisplayOrder = 6,
                CreatedAt = DateTime.UtcNow
            },

            // Format settings
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "date_format",
                Value = "dd-MMM-yyyy",
                DataType = "string",
                Description = "Default date display format",
                Category = "Formatting",
                IsEditable = true,
                DisplayOrder = 7,
                CreatedAt = DateTime.UtcNow
            },
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "number_format",
                Value = "#,##0.00",
                DataType = "string",
                Description = "Default number display format",
                Category = "Formatting",
                IsEditable = true,
                DisplayOrder = 8,
                CreatedAt = DateTime.UtcNow
            },

            // Notification settings
            new SystemSetting
            {
                Id = Guid.NewGuid(),
                Key = "deadline_reminder_days",
                Value = "3,1",
                DataType = "string",
                Description = "Days before deadline to send reminders (comma-separated)",
                Category = "Notifications",
                IsEditable = true,
                DisplayOrder = 9,
                CreatedAt = DateTime.UtcNow
            }
        };

        await _context.SystemSettings.AddRangeAsync(systemSettings);
        await _context.SaveChangesAsync();

        _logger.LogInformation("Seeded {Count} system settings", systemSettings.Count);
    }

    /// <summary>
    /// Seeds demo users for development and testing.
    /// Default password for all users: Bayan@2024
    /// </summary>
    private async Task SeedDemoUsersAsync()
    {
        if (await _context.Users.AnyAsync())
        {
            _logger.LogInformation("Users already seeded, skipping...");
            return;
        }

        _logger.LogInformation("Seeding demo users...");

        var demoUsers = new List<User>
        {
            // System Administrator
            new User
            {
                Id = Guid.NewGuid(),
                Email = "admin@bayan.ae",
                PasswordHash = DefaultPasswordHash,
                FirstName = "System",
                LastName = "Administrator",
                Role = UserRole.Admin,
                IsActive = true,
                EmailVerified = true,
                Department = "IT",
                JobTitle = "System Administrator",
                PreferredLanguage = "en",
                TimeZone = "Asia/Dubai",
                CreatedAt = DateTime.UtcNow
            },

            // Tender Manager
            new User
            {
                Id = Guid.NewGuid(),
                Email = "tendermgr@bayan.ae",
                PasswordHash = DefaultPasswordHash,
                FirstName = "Ahmad",
                LastName = "Al-Rashid",
                Role = UserRole.TenderManager,
                IsActive = true,
                EmailVerified = true,
                Department = "Procurement",
                JobTitle = "Tender Manager",
                PreferredLanguage = "ar",
                TimeZone = "Asia/Dubai",
                CreatedAt = DateTime.UtcNow
            },

            // Commercial Analyst
            new User
            {
                Id = Guid.NewGuid(),
                Email = "analyst@bayan.ae",
                PasswordHash = DefaultPasswordHash,
                FirstName = "Fatima",
                LastName = "Hassan",
                Role = UserRole.CommercialAnalyst,
                IsActive = true,
                EmailVerified = true,
                Department = "Commercial",
                JobTitle = "Commercial Analyst",
                PreferredLanguage = "en",
                TimeZone = "Asia/Dubai",
                CreatedAt = DateTime.UtcNow
            },

            // Technical Panelist
            new User
            {
                Id = Guid.NewGuid(),
                Email = "panelist1@bayan.ae",
                PasswordHash = DefaultPasswordHash,
                FirstName = "Mohammed",
                LastName = "Al-Farsi",
                Role = UserRole.TechnicalPanelist,
                IsActive = true,
                EmailVerified = true,
                Department = "Technical",
                JobTitle = "Senior Engineer",
                PreferredLanguage = "ar",
                TimeZone = "Asia/Dubai",
                CreatedAt = DateTime.UtcNow
            },

            // Approver
            new User
            {
                Id = Guid.NewGuid(),
                Email = "approver@bayan.ae",
                PasswordHash = DefaultPasswordHash,
                FirstName = "Khalid",
                LastName = "Al-Mansour",
                Role = UserRole.Approver,
                IsActive = true,
                EmailVerified = true,
                Department = "Executive",
                JobTitle = "Director of Procurement",
                PreferredLanguage = "en",
                TimeZone = "Asia/Dubai",
                CreatedAt = DateTime.UtcNow
            },

            // Auditor
            new User
            {
                Id = Guid.NewGuid(),
                Email = "auditor@bayan.ae",
                PasswordHash = DefaultPasswordHash,
                FirstName = "Sara",
                LastName = "Al-Ahmed",
                Role = UserRole.Auditor,
                IsActive = true,
                EmailVerified = true,
                Department = "Audit",
                JobTitle = "Internal Auditor",
                PreferredLanguage = "en",
                TimeZone = "Asia/Dubai",
                CreatedAt = DateTime.UtcNow
            },

            // Bidder (External vendor)
            new User
            {
                Id = Guid.NewGuid(),
                Email = "bidder@vendor.ae",
                PasswordHash = DefaultPasswordHash,
                FirstName = "Ali",
                LastName = "Contractor",
                Role = UserRole.Bidder,
                IsActive = true,
                EmailVerified = true,
                CompanyName = "ABC Construction LLC",
                CommercialRegistrationNumber = "CR-12345",
                PreferredLanguage = "en",
                TimeZone = "Asia/Dubai",
                CreatedAt = DateTime.UtcNow
            }
        };

        await _context.Users.AddRangeAsync(demoUsers);
        await _context.SaveChangesAsync();

        _logger.LogInformation("Seeded {Count} demo users", demoUsers.Count);
        _logger.LogInformation("Default password for all demo users: Bayan@2024");
    }

    /// <summary>
    /// Seeds demo bidders for development and testing.
    /// These are portal-facing entities (separate from Users) that allow
    /// external vendors to log in via the bidder portal.
    /// Default password: Bayan@2024
    /// </summary>
    private async Task SeedDemoBiddersAsync()
    {
        if (await _context.Bidders.AnyAsync(b => b.Email == "bidder@vendor.ae"))
        {
            _logger.LogInformation("Demo bidders already seeded, skipping...");
            return;
        }

        _logger.LogInformation("Seeding demo bidders...");

        var demoBidders = new List<Bidder>
        {
            new Bidder
            {
                Id = Guid.NewGuid(),
                CompanyName = "ABC Construction LLC",
                CRNumber = "CR-12345",
                LicenseNumber = "TL-2024-001",
                ContactPerson = "Ali Contractor",
                Email = "bidder@vendor.ae",
                Phone = "+971-50-1234567",
                TradeSpecialization = "General Construction",
                PrequalificationStatus = PrequalificationStatus.Qualified,
                IsActive = true,
                PasswordHash = DefaultPasswordHash,
                CreatedAt = DateTime.UtcNow
            },
            new Bidder
            {
                Id = Guid.NewGuid(),
                CompanyName = "Gulf MEP Services",
                CRNumber = "CR-67890",
                LicenseNumber = "TL-2024-002",
                ContactPerson = "Hassan Al-Noor",
                Email = "bidder2@vendor.ae",
                Phone = "+971-50-9876543",
                TradeSpecialization = "MEP Works",
                PrequalificationStatus = PrequalificationStatus.Qualified,
                IsActive = true,
                PasswordHash = DefaultPasswordHash,
                CreatedAt = DateTime.UtcNow
            }
        };

        await _context.Bidders.AddRangeAsync(demoBidders);
        await _context.SaveChangesAsync();

        _logger.LogInformation("Seeded {Count} demo bidders", demoBidders.Count);
        _logger.LogInformation("Default password for all demo bidders: Bayan@2024");
    }

    /// <summary>
    /// Generates a BCrypt hash for a given password.
    /// Use this method to generate new password hashes if needed.
    /// </summary>
    /// <param name="password">The plain text password to hash</param>
    /// <returns>BCrypt hashed password</returns>
    public static string HashPassword(string password)
    {
        return BCrypt.Net.BCrypt.HashPassword(password, 12);
    }
}
