using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bayan.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddClientDetailFields : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'clients' AND column_name = 'city'
                    ) THEN
                        ALTER TABLE clients ADD COLUMN city varchar(100);
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'clients' AND column_name = 'country'
                    ) THEN
                        ALTER TABLE clients ADD COLUMN country varchar(100);
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'clients' AND column_name = 'cr_number'
                    ) THEN
                        ALTER TABLE clients ADD COLUMN cr_number varchar(100);
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'clients' AND column_name = 'vat_number'
                    ) THEN
                        ALTER TABLE clients ADD COLUMN vat_number varchar(100);
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'clients' AND column_name = 'contact_email'
                    ) THEN
                        ALTER TABLE clients ADD COLUMN contact_email varchar(255);
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'clients' AND column_name = 'contact_phone'
                    ) THEN
                        ALTER TABLE clients ADD COLUMN contact_phone varchar(50);
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE clients DROP COLUMN IF EXISTS city;
                ALTER TABLE clients DROP COLUMN IF EXISTS country;
                ALTER TABLE clients DROP COLUMN IF EXISTS cr_number;
                ALTER TABLE clients DROP COLUMN IF EXISTS vat_number;
                ALTER TABLE clients DROP COLUMN IF EXISTS contact_email;
                ALTER TABLE clients DROP COLUMN IF EXISTS contact_phone;
            ");
        }
    }
}
