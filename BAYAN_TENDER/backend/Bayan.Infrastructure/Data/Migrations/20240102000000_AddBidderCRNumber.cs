using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bayan.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddBidderCRNumber : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Comprehensive schema alignment: adds ALL columns that entity configurations
            // define but the initial migration missed.
            // All operations are idempotent (IF NOT EXISTS).

            migrationBuilder.Sql(@"
                DO $$
                BEGIN
                    -- =============================================
                    -- 1. bidders: add cr_number
                    -- =============================================
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'bidders' AND column_name = 'cr_number'
                    ) THEN
                        ALTER TABLE bidders ADD COLUMN cr_number character varying(100);
                    END IF;

                    -- =============================================
                    -- 2. clarifications: add assigned_to_id
                    -- =============================================
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'clarifications' AND column_name = 'assigned_to_id'
                    ) THEN
                        ALTER TABLE clarifications ADD COLUMN assigned_to_id uuid;
                    END IF;

                    -- =============================================
                    -- 3. tender_bidders: add missing timestamp columns
                    -- =============================================
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'tender_bidders' AND column_name = 'invitation_sent_at'
                    ) THEN
                        ALTER TABLE tender_bidders ADD COLUMN invitation_sent_at timestamp with time zone;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'tender_bidders' AND column_name = 'invitation_opened_at'
                    ) THEN
                        ALTER TABLE tender_bidders ADD COLUMN invitation_opened_at timestamp with time zone;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'tender_bidders' AND column_name = 'registered_at'
                    ) THEN
                        ALTER TABLE tender_bidders ADD COLUMN registered_at timestamp with time zone;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'tender_bidders' AND column_name = 'nda_signed_date'
                    ) THEN
                        ALTER TABLE tender_bidders ADD COLUMN nda_signed_date timestamp with time zone;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'tender_bidders' AND column_name = 'nda_expiry_date'
                    ) THEN
                        ALTER TABLE tender_bidders ADD COLUMN nda_expiry_date timestamp with time zone;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'tender_bidders' AND column_name = 'qualified_at'
                    ) THEN
                        ALTER TABLE tender_bidders ADD COLUMN qualified_at timestamp with time zone;
                    END IF;

                    -- =============================================
                    -- 4. approval_levels: add updated_at
                    -- =============================================
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'approval_levels' AND column_name = 'updated_at'
                    ) THEN
                        ALTER TABLE approval_levels ADD COLUMN updated_at timestamp with time zone;
                    END IF;

                    -- =============================================
                    -- 5. evaluation_state table (singular)
                    --    Config maps to 'evaluation_state' but migration
                    --    created 'evaluation_states' with different schema.
                    --    Create the correct table if it doesn't exist.
                    -- =============================================
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'evaluation_state'
                    ) THEN
                        CREATE TABLE evaluation_state (
                            id uuid NOT NULL,
                            tender_id uuid NOT NULL,
                            scoring_method character varying(20) NOT NULL DEFAULT 'Numeric',
                            blind_mode boolean NOT NULL DEFAULT true,
                            technical_evaluation_deadline timestamp with time zone,
                            technical_scores_locked boolean NOT NULL DEFAULT false,
                            technical_locked_at timestamp with time zone,
                            technical_locked_by uuid,
                            commercial_scores_calculated boolean NOT NULL DEFAULT false,
                            combined_scores_calculated boolean NOT NULL DEFAULT false,
                            created_at timestamp with time zone NOT NULL,
                            updated_at timestamp with time zone,
                            CONSTRAINT ""PK_evaluation_state"" PRIMARY KEY (id),
                            CONSTRAINT ""FK_evaluation_state_tenders_tender_id"" FOREIGN KEY (tender_id) REFERENCES tenders(id) ON DELETE CASCADE
                        );
                        CREATE UNIQUE INDEX ""IX_evaluation_state_tender_id"" ON evaluation_state (tender_id);
                    END IF;

                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                DROP TABLE IF EXISTS evaluation_state;
                ALTER TABLE approval_levels DROP COLUMN IF EXISTS updated_at;
                ALTER TABLE tender_bidders DROP COLUMN IF EXISTS invitation_sent_at;
                ALTER TABLE tender_bidders DROP COLUMN IF EXISTS invitation_opened_at;
                ALTER TABLE tender_bidders DROP COLUMN IF EXISTS registered_at;
                ALTER TABLE tender_bidders DROP COLUMN IF EXISTS nda_signed_date;
                ALTER TABLE tender_bidders DROP COLUMN IF EXISTS nda_expiry_date;
                ALTER TABLE tender_bidders DROP COLUMN IF EXISTS qualified_at;
                ALTER TABLE clarifications DROP COLUMN IF EXISTS assigned_to_id;
                ALTER TABLE bidders DROP COLUMN IF EXISTS cr_number;
            ");
        }
    }
}
