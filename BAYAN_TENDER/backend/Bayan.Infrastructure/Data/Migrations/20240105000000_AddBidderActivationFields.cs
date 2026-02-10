using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bayan.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddBidderActivationFields : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    -- Add activation_token column to bidders table
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'bidders' AND column_name = 'activation_token'
                    ) THEN
                        ALTER TABLE bidders ADD COLUMN activation_token character varying(500);
                    END IF;

                    -- Add activation_token_expiry column to bidders table
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'bidders' AND column_name = 'activation_token_expiry'
                    ) THEN
                        ALTER TABLE bidders ADD COLUMN activation_token_expiry timestamp with time zone;
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE bidders DROP COLUMN IF EXISTS activation_token;
                ALTER TABLE bidders DROP COLUMN IF EXISTS activation_token_expiry;
            ");
        }
    }
}
