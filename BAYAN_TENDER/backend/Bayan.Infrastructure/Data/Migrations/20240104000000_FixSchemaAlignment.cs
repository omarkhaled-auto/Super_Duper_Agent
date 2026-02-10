using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bayan.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class FixSchemaAlignment : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Bakes e2e/schema-fixes.sql into a proper EF Core migration.
            // All operations are idempotent so this is safe to run on existing DBs.

            migrationBuilder.Sql(@"
                -- bid_documents: add missing uploaded_at + defaults
                ALTER TABLE bid_documents ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
                ALTER TABLE bid_documents ALTER COLUMN created_at SET DEFAULT NOW();

                -- evaluation_panels: add missing completed_at, set defaults
                ALTER TABLE evaluation_panels ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;
                ALTER TABLE evaluation_panels ALTER COLUMN created_at SET DEFAULT NOW();

                -- evaluation_state + approval tables: ensure defaults
                DO $$ BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'evaluation_state') THEN
                        ALTER TABLE evaluation_state ALTER COLUMN created_at SET DEFAULT NOW();
                    END IF;
                END $$;
                ALTER TABLE approval_levels ALTER COLUMN created_at SET DEFAULT NOW();
                ALTER TABLE approval_workflows ALTER COLUMN created_at SET DEFAULT NOW();
            ");

            // Make evaluation_panels extra columns nullable
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='evaluation_panels' AND column_name='role' AND is_nullable='NO'
                    ) THEN
                        ALTER TABLE evaluation_panels ALTER COLUMN role DROP NOT NULL;
                        ALTER TABLE evaluation_panels ALTER COLUMN role SET DEFAULT 'Panelist';
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='evaluation_panels' AND column_name='assigned_by' AND is_nullable='NO'
                    ) THEN
                        ALTER TABLE evaluation_panels ALTER COLUMN assigned_by DROP NOT NULL;
                    END IF;
                END $$;
            ");

            // Rename user_id to panelist_user_id if needed
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='evaluation_panels' AND column_name='user_id'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='evaluation_panels' AND column_name='panelist_user_id'
                    ) THEN
                        DROP INDEX IF EXISTS ""IX_evaluation_panels_tender_id_user_id"";
                        ALTER TABLE evaluation_panels RENAME COLUMN user_id TO panelist_user_id;
                        CREATE UNIQUE INDEX IF NOT EXISTS ""IX_evaluation_panels_tender_id_panelist_user_id""
                            ON evaluation_panels (tender_id, panelist_user_id);
                    END IF;
                END $$;
            ");

            // Recreate technical_scores if schema is wrong (has bid_submission_id instead of tender_id)
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='technical_scores' AND column_name='bid_submission_id'
                    ) THEN
                        DROP TABLE IF EXISTS technical_scores CASCADE;
                        CREATE TABLE technical_scores (
                            id UUID NOT NULL PRIMARY KEY,
                            tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
                            bidder_id UUID NOT NULL REFERENCES bidders(id) ON DELETE RESTRICT,
                            panelist_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                            criterion_id UUID NOT NULL REFERENCES evaluation_criteria(id) ON DELETE RESTRICT,
                            score NUMERIC(4,1) NOT NULL DEFAULT 0,
                            comment TEXT,
                            is_draft BOOLEAN NOT NULL DEFAULT TRUE,
                            submitted_at TIMESTAMP WITH TIME ZONE,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE
                        );
                        CREATE UNIQUE INDEX ""IX_technical_scores_tender_bidder_panelist_criterion""
                            ON technical_scores (tender_id, bidder_id, panelist_user_id, criterion_id);
                        CREATE INDEX ""IX_technical_scores_tender_id"" ON technical_scores (tender_id);
                        CREATE INDEX ""IX_technical_scores_tender_bidder"" ON technical_scores (tender_id, bidder_id);
                    END IF;
                END $$;
            ");

            // Recreate commercial_scores if schema is wrong
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='commercial_scores' AND column_name='bid_submission_id'
                    ) THEN
                        DROP TABLE IF EXISTS commercial_scores CASCADE;
                        CREATE TABLE commercial_scores (
                            id UUID NOT NULL PRIMARY KEY,
                            tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
                            bidder_id UUID NOT NULL REFERENCES bidders(id) ON DELETE RESTRICT,
                            normalized_total_price NUMERIC(18,2) NOT NULL DEFAULT 0,
                            commercial_score NUMERIC(6,2) NOT NULL DEFAULT 0,
                            rank INTEGER NOT NULL DEFAULT 0,
                            include_provisional_sums BOOLEAN NOT NULL DEFAULT FALSE,
                            include_alternates BOOLEAN NOT NULL DEFAULT FALSE,
                            calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        );
                        CREATE UNIQUE INDEX ""IX_commercial_scores_tender_bidder""
                            ON commercial_scores (tender_id, bidder_id);
                    END IF;
                END $$;
            ");

            // Recreate combined_scorecards if schema is wrong
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='combined_scorecards' AND column_name='bid_submission_id'
                    ) THEN
                        DROP TABLE IF EXISTS combined_scorecards CASCADE;
                        CREATE TABLE combined_scorecards (
                            id UUID NOT NULL PRIMARY KEY,
                            tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
                            bidder_id UUID NOT NULL REFERENCES bidders(id) ON DELETE RESTRICT,
                            technical_score_avg NUMERIC(6,2) NOT NULL DEFAULT 0,
                            technical_rank INTEGER NOT NULL DEFAULT 0,
                            commercial_score NUMERIC(6,2) NOT NULL DEFAULT 0,
                            commercial_rank INTEGER NOT NULL DEFAULT 0,
                            technical_weight INTEGER NOT NULL DEFAULT 0,
                            commercial_weight INTEGER NOT NULL DEFAULT 0,
                            combined_score NUMERIC(6,2) NOT NULL DEFAULT 0,
                            final_rank INTEGER NOT NULL DEFAULT 0,
                            is_recommended BOOLEAN NOT NULL DEFAULT FALSE,
                            calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        );
                        CREATE UNIQUE INDEX ""IX_combined_scorecards_tender_bidder""
                            ON combined_scorecards (tender_id, bidder_id);
                    END IF;
                END $$;
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            // Down migration is best-effort; these are alignment fixes
            migrationBuilder.Sql(@"
                ALTER TABLE bid_documents DROP COLUMN IF EXISTS uploaded_at;
                ALTER TABLE evaluation_panels DROP COLUMN IF EXISTS completed_at;
            ");
        }
    }
}
