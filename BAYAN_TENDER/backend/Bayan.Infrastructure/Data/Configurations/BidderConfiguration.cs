using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class BidderConfiguration : IEntityTypeConfiguration<Bidder>
{
    public void Configure(EntityTypeBuilder<Bidder> builder)
    {
        builder.ToTable("bidders");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.Email);
        builder.HasIndex(e => e.TradeSpecialization);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.CompanyName)
            .HasColumnName("company_name")
            .HasMaxLength(300)
            .IsRequired();

        builder.Property(e => e.CRNumber)
            .HasColumnName("cr_number")
            .HasMaxLength(100);

        builder.Property(e => e.LicenseNumber)
            .HasColumnName("license_number")
            .HasMaxLength(100);

        builder.Property(e => e.ContactPerson)
            .HasColumnName("contact_person")
            .HasMaxLength(200)
            .IsRequired();

        builder.Property(e => e.Email)
            .HasColumnName("email")
            .HasMaxLength(255)
            .IsRequired();

        builder.Property(e => e.Phone)
            .HasColumnName("phone")
            .HasMaxLength(50);

        builder.Property(e => e.TradeSpecialization)
            .HasColumnName("trade_specialization")
            .HasMaxLength(200);

        builder.Property(e => e.PrequalificationStatus)
            .HasColumnName("prequalification_status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValueSql("'Pending'");

        builder.Property(e => e.CompanyProfilePath)
            .HasColumnName("company_profile_path")
            .HasMaxLength(1000);

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active")
            .HasDefaultValue(true);

        builder.Property(e => e.PasswordHash)
            .HasColumnName("password_hash")
            .HasMaxLength(500);

        builder.Property(e => e.LastLoginAt)
            .HasColumnName("last_login_at");

        builder.Property(e => e.ActivationToken)
            .HasColumnName("activation_token")
            .HasMaxLength(500);

        builder.Property(e => e.ActivationTokenExpiry)
            .HasColumnName("activation_token_expiry");

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");
    }
}
