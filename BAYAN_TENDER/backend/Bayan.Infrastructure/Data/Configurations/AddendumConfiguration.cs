using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class AddendumConfiguration : IEntityTypeConfiguration<Addendum>
{
    public void Configure(EntityTypeBuilder<Addendum> builder)
    {
        builder.ToTable("addenda");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.AddendumNumber }).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.AddendumNumber)
            .HasColumnName("addendum_number")
            .IsRequired();

        builder.Property(e => e.IssueDate)
            .HasColumnName("issue_date")
            .IsRequired();

        builder.Property(e => e.Summary)
            .HasColumnName("summary")
            .IsRequired();

        builder.Property(e => e.ExtendsDeadline)
            .HasColumnName("extends_deadline")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.NewDeadline)
            .HasColumnName("new_deadline");

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValueSql("'Draft'")
            .IsRequired();

        builder.Property(e => e.IssuedBy)
            .HasColumnName("issued_by");

        builder.Property(e => e.IssuedAt)
            .HasColumnName("issued_at");

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.Addenda)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Issuer)
            .WithMany(u => u.IssuedAddenda)
            .HasForeignKey(e => e.IssuedBy)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
