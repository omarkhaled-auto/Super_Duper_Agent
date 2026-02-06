using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.ToTable("users");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.Email).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.Email)
            .HasColumnName("email")
            .HasMaxLength(255)
            .IsRequired();

        builder.Property(e => e.PasswordHash)
            .HasColumnName("password_hash")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(e => e.FirstName)
            .HasColumnName("first_name")
            .HasMaxLength(100)
            .IsRequired();

        builder.Property(e => e.LastName)
            .HasColumnName("last_name")
            .HasMaxLength(100)
            .IsRequired();

        builder.Property(e => e.PhoneNumber)
            .HasColumnName("phone")
            .HasMaxLength(50);

        builder.Property(e => e.Role)
            .HasColumnName("role")
            .HasMaxLength(50)
            .HasConversion<string>()
            .IsRequired();

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active")
            .HasDefaultValue(true);

        builder.Property(e => e.LastLoginAt)
            .HasColumnName("last_login_at");

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Additional fields that extend the base schema
        builder.Property(e => e.EmailVerified)
            .HasColumnName("email_verified")
            .HasDefaultValue(false);

        builder.Property(e => e.EmailVerificationToken)
            .HasColumnName("email_verification_token")
            .HasMaxLength(500);

        builder.Property(e => e.EmailVerificationTokenExpiry)
            .HasColumnName("email_verification_token_expiry");

        builder.Property(e => e.PasswordResetToken)
            .HasColumnName("password_reset_token")
            .HasMaxLength(500);

        builder.Property(e => e.PasswordResetTokenExpiry)
            .HasColumnName("password_reset_token_expiry");

        builder.Property(e => e.FailedLoginAttempts)
            .HasColumnName("failed_login_attempts")
            .HasDefaultValue(0);

        builder.Property(e => e.LockoutEnd)
            .HasColumnName("lockout_end");

        builder.Property(e => e.RefreshToken)
            .HasColumnName("refresh_token")
            .HasMaxLength(500);

        builder.Property(e => e.RefreshTokenExpiry)
            .HasColumnName("refresh_token_expiry");

        builder.Property(e => e.CompanyName)
            .HasColumnName("company_name")
            .HasMaxLength(300);

        builder.Property(e => e.CommercialRegistrationNumber)
            .HasColumnName("commercial_registration_number")
            .HasMaxLength(100);

        builder.Property(e => e.Department)
            .HasColumnName("department")
            .HasMaxLength(100);

        builder.Property(e => e.JobTitle)
            .HasColumnName("job_title")
            .HasMaxLength(100);

        builder.Property(e => e.ProfilePictureUrl)
            .HasColumnName("profile_picture_url")
            .HasMaxLength(1000);

        builder.Property(e => e.PreferredLanguage)
            .HasColumnName("preferred_language")
            .HasMaxLength(10)
            .HasDefaultValue("ar");

        builder.Property(e => e.TimeZone)
            .HasColumnName("timezone")
            .HasMaxLength(50)
            .HasDefaultValue("Asia/Riyadh");

        // Ignore computed properties
        builder.Ignore(e => e.FullName);
        builder.Ignore(e => e.CreatedBy);
        builder.Ignore(e => e.LastModifiedBy);
        builder.Ignore(e => e.LastModifiedAt);
    }
}
