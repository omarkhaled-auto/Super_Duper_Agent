using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class EvaluationPanelConfiguration : IEntityTypeConfiguration<EvaluationPanel>
{
    public void Configure(EntityTypeBuilder<EvaluationPanel> builder)
    {
        builder.ToTable("evaluation_panels");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.PanelistUserId }).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.PanelistUserId)
            .HasColumnName("panelist_user_id")
            .IsRequired();

        builder.Property(e => e.AssignedAt)
            .HasColumnName("assigned_at")
            .IsRequired();

        builder.Property(e => e.CompletedAt)
            .HasColumnName("completed_at");

        builder.Ignore(e => e.CreatedAt);
        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.EvaluationPanels)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Panelist)
            .WithMany(u => u.EvaluationPanels)
            .HasForeignKey(e => e.PanelistUserId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
