using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class ClientConfiguration : IEntityTypeConfiguration<Client>
{
    public void Configure(EntityTypeBuilder<Client> builder)
    {
        builder.ToTable("clients");

        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .HasMaxLength(300)
            .IsRequired();

        builder.Property(e => e.ContactPerson)
            .HasColumnName("contact_person")
            .HasMaxLength(200);

        builder.Property(e => e.Email)
            .HasColumnName("email")
            .HasMaxLength(255);

        builder.Property(e => e.Phone)
            .HasColumnName("phone")
            .HasMaxLength(50);

        builder.Property(e => e.Address)
            .HasColumnName("address");

        builder.Property(e => e.City)
            .HasColumnName("city")
            .HasMaxLength(100);

        builder.Property(e => e.Country)
            .HasColumnName("country")
            .HasMaxLength(100);

        builder.Property(e => e.CRNumber)
            .HasColumnName("cr_number")
            .HasMaxLength(100);

        builder.Property(e => e.VatNumber)
            .HasColumnName("vat_number")
            .HasMaxLength(100);

        builder.Property(e => e.ContactEmail)
            .HasColumnName("contact_email")
            .HasMaxLength(255);

        builder.Property(e => e.ContactPhone)
            .HasColumnName("contact_phone")
            .HasMaxLength(50);

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active")
            .HasDefaultValue(true);

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Ignore audit fields not in schema
        builder.Ignore(e => e.CreatedBy);
        builder.Ignore(e => e.LastModifiedBy);
        builder.Ignore(e => e.LastModifiedAt);
    }
}
