using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class ApprovalWorkflowConfiguration : IEntityTypeConfiguration<ApprovalWorkflow>
{
    public void Configure(EntityTypeBuilder<ApprovalWorkflow> builder)
    {
        builder.ToTable("approval_workflows");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.TenderId).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValueSql("'Pending'")
            .IsRequired();

        builder.Property(e => e.InitiatedBy)
            .HasColumnName("initiated_by")
            .IsRequired();

        builder.Property(e => e.InitiatedAt)
            .HasColumnName("initiated_at")
            .IsRequired();

        builder.Property(e => e.CompletedAt)
            .HasColumnName("completed_at");

        builder.Property(e => e.AwardPackPdfPath)
            .HasColumnName("award_pack_pdf_path")
            .HasMaxLength(1000);

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithOne(t => t.ApprovalWorkflow)
            .HasForeignKey<ApprovalWorkflow>(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Initiator)
            .WithMany(u => u.InitiatedWorkflows)
            .HasForeignKey(e => e.InitiatedBy)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
