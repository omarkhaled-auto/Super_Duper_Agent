using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class BidderRefreshTokenConfiguration : IEntityTypeConfiguration<BidderRefreshToken>
{
    public void Configure(EntityTypeBuilder<BidderRefreshToken> builder)
    {
        builder.ToTable("bidder_refresh_tokens");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.Token).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.BidderId)
            .HasColumnName("bidder_id")
            .IsRequired();

        builder.Property(e => e.Token)
            .HasColumnName("token")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(e => e.ExpiresAt)
            .HasColumnName("expires_at")
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.RevokedAt)
            .HasColumnName("revoked_at");

        builder.Property(e => e.IsRevoked)
            .HasColumnName("is_revoked")
            .HasDefaultValue(false);

        builder.Property(e => e.CreatedByIp)
            .HasColumnName("created_by_ip")
            .HasMaxLength(50);

        builder.Property(e => e.RevokedByIp)
            .HasColumnName("revoked_by_ip")
            .HasMaxLength(50);

        builder.Property(e => e.ReplacedByToken)
            .HasColumnName("replaced_by_token")
            .HasMaxLength(500);

        // Ignore computed properties
        builder.Ignore(e => e.IsExpired);
        builder.Ignore(e => e.IsActive);
        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Bidder)
            .WithMany()
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
