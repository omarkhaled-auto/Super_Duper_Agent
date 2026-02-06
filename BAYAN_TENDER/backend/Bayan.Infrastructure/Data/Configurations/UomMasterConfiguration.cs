using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class UomMasterConfiguration : IEntityTypeConfiguration<UomMaster>
{
    public void Configure(EntityTypeBuilder<UomMaster> builder)
    {
        builder.ToTable("uom_master");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.Code).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .HasMaxLength(20)
            .IsRequired();

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .HasMaxLength(100)
            .IsRequired();

        builder.Property(e => e.Category)
            .HasColumnName("category")
            .HasMaxLength(50)
            .HasConversion<string>()
            .IsRequired();

        builder.Property(e => e.BaseUnitCode)
            .HasColumnName("base_unit_code")
            .HasMaxLength(20);

        builder.Property(e => e.ConversionToBase)
            .HasColumnName("conversion_to_base")
            .HasPrecision(18, 10);

        builder.Property(e => e.IsSystem)
            .HasColumnName("is_system")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Ignore(e => e.UpdatedAt);
    }
}
