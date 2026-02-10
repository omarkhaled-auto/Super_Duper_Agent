using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bayan.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddTenderEstimatedValue : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'tenders' AND column_name = 'estimated_value'
                    ) THEN
                        ALTER TABLE tenders ADD COLUMN estimated_value numeric(18,2);
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE tenders DROP COLUMN IF EXISTS estimated_value;
            ");
        }
    }
}
