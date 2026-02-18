using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class TenderConfiguration : IEntityTypeConfiguration<Tender>
{
    public void Configure(EntityTypeBuilder<Tender> builder)
    {
        builder.ToTable("tenders");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.Reference).IsUnique();
        builder.HasIndex(e => e.Status);
        builder.HasIndex(e => e.ClientId);
        builder.HasIndex(e => e.CreatedBy);
        builder.HasIndex(e => e.SubmissionDeadline);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.Title)
            .HasColumnName("title")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(e => e.Reference)
            .HasColumnName("reference")
            .HasMaxLength(100)
            .IsRequired();

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(4000);

        builder.Property(e => e.ClientId)
            .HasColumnName("client_id")
            .IsRequired();

        builder.Property(e => e.TenderType)
            .HasColumnName("tender_type")
            .HasMaxLength(50)
            .HasConversion<string>()
            .IsRequired();

        builder.Property(e => e.BaseCurrency)
            .HasColumnName("base_currency")
            .HasMaxLength(3)
            .HasDefaultValue("AED")
            .IsRequired();

        builder.Property(e => e.EstimatedValue)
            .HasColumnName("estimated_value")
            .HasColumnType("numeric(18,2)");

        builder.Property(e => e.BidValidityDays)
            .HasColumnName("bid_validity_days")
            .HasDefaultValue(90)
            .IsRequired();

        builder.Property(e => e.IssueDate)
            .HasColumnName("issue_date")
            .IsRequired();

        builder.Property(e => e.ClarificationDeadline)
            .HasColumnName("clarification_deadline")
            .IsRequired();

        builder.Property(e => e.SubmissionDeadline)
            .HasColumnName("submission_deadline")
            .IsRequired();

        builder.Property(e => e.OpeningDate)
            .HasColumnName("opening_date")
            .IsRequired();

        builder.Property(e => e.TechnicalWeight)
            .HasColumnName("technical_weight")
            .HasDefaultValue(40)
            .IsRequired();

        builder.Property(e => e.CommercialWeight)
            .HasColumnName("commercial_weight")
            .HasDefaultValue(60)
            .IsRequired();

        builder.Property(e => e.PricingLevel)
            .HasColumnName("pricing_level")
            .HasMaxLength(20)
            .HasConversion<string>()
            .HasDefaultValueSql("'SubItem'")
            .IsRequired();

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValueSql("'Draft'")
            .IsRequired();

        builder.Property(e => e.CreatedBy)
            .HasColumnName("created_by")
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        builder.Property(e => e.PublishedAt)
            .HasColumnName("published_at");

        builder.Property(e => e.AwardedAt)
            .HasColumnName("awarded_at");

        // Ignore audit fields
        builder.Ignore(e => e.LastModifiedBy);
        builder.Ignore(e => e.LastModifiedAt);

        // Relationships
        builder.HasOne(e => e.Client)
            .WithMany(c => c.Tenders)
            .HasForeignKey(e => e.ClientId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.Creator)
            .WithMany(u => u.CreatedTenders)
            .HasForeignKey(e => e.CreatedBy)
            .OnDelete(DeleteBehavior.Restrict);

        // Check constraints would be added via migration
        // CONSTRAINT chk_weights CHECK (technical_weight + commercial_weight = 100)
        // CONSTRAINT chk_clarification_before_submission CHECK (clarification_deadline < submission_deadline)
        // CONSTRAINT chk_dates_order CHECK (issue_date <= clarification_deadline AND clarification_deadline < submission_deadline)
    }
}
