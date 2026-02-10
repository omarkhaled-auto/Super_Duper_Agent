using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bayan.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddQualificationReason : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'tender_bidders' AND column_name = 'qualification_reason'
                    ) THEN
                        ALTER TABLE tender_bidders ADD COLUMN qualification_reason character varying(1000);
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE tender_bidders DROP COLUMN IF EXISTS qualification_reason;
            ");
        }
    }
}
