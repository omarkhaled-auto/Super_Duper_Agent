using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bayan.Infrastructure.Data.Migrations
{
    /// <summary>
    /// Consolidates all schema fixes from e2e/schema-fixes.sql into a proper EF migration.
    /// Fixes orphan NOT NULL columns, missing tables, wrong column types, and missing defaults
    /// that were gaps between EF entity configs and the InitialCreate migration.
    /// All statements are idempotent (IF EXISTS / IF NOT EXISTS) for safe re-runs.
    /// </summary>
    public partial class ConsolidateSchemaFixes : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // 1. tender_bidders: invited_at/invited_by are orphan NOT NULL columns
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tender_bidders' AND column_name='invited_at' AND is_nullable='NO') THEN
                    ALTER TABLE tender_bidders ALTER COLUMN invited_at SET DEFAULT NOW();
                    ALTER TABLE tender_bidders ALTER COLUMN invited_at DROP NOT NULL;
                  END IF;
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tender_bidders' AND column_name='invited_by' AND is_nullable='NO') THEN
                    ALTER TABLE tender_bidders ALTER COLUMN invited_by DROP NOT NULL;
                  END IF;
                END $$;
            ");

            // 2. bidder_refresh_tokens: table missing from EF migrations
            migrationBuilder.Sql(@"
                CREATE TABLE IF NOT EXISTS bidder_refresh_tokens (
                  id UUID NOT NULL PRIMARY KEY,
                  bidder_id UUID NOT NULL REFERENCES bidders(id) ON DELETE CASCADE,
                  token VARCHAR(500) NOT NULL,
                  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                  revoked_at TIMESTAMP WITH TIME ZONE,
                  is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
                  created_by_ip VARCHAR(50),
                  revoked_by_ip VARCHAR(50),
                  replaced_by_token VARCHAR(500)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS ""IX_bidder_refresh_tokens_token"" ON bidder_refresh_tokens (token);
                CREATE INDEX IF NOT EXISTS ""IX_bidder_refresh_tokens_bidder_id"" ON bidder_refresh_tokens (bidder_id);
            ");

            // 3. bid_documents: missing uploaded_at + defaults
            migrationBuilder.Sql(@"
                ALTER TABLE bid_documents ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
                ALTER TABLE bid_documents ALTER COLUMN created_at SET DEFAULT NOW();
            ");

            // 4. evaluation_panels: missing completed_at, fix nullable cols
            migrationBuilder.Sql(@"
                ALTER TABLE evaluation_panels ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;
                ALTER TABLE evaluation_panels ALTER COLUMN created_at SET DEFAULT NOW();
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='evaluation_panels' AND column_name='role' AND is_nullable='NO') THEN
                    ALTER TABLE evaluation_panels ALTER COLUMN role DROP NOT NULL;
                    ALTER TABLE evaluation_panels ALTER COLUMN role SET DEFAULT 'Panelist';
                  END IF;
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='evaluation_panels' AND column_name='assigned_by' AND is_nullable='NO') THEN
                    ALTER TABLE evaluation_panels ALTER COLUMN assigned_by DROP NOT NULL;
                  END IF;
                END $$;
            ");

            // 5. Rename evaluation_panels.user_id to panelist_user_id if needed
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='evaluation_panels' AND column_name='user_id')
                     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='evaluation_panels' AND column_name='panelist_user_id') THEN
                    DROP INDEX IF EXISTS ""IX_evaluation_panels_tender_id_user_id"";
                    ALTER TABLE evaluation_panels RENAME COLUMN user_id TO panelist_user_id;
                    CREATE UNIQUE INDEX IF NOT EXISTS ""IX_evaluation_panels_tender_id_panelist_user_id"" ON evaluation_panels (tender_id, panelist_user_id);
                  END IF;
                END $$;
            ");

            // 6. evaluation_state + approval tables: ensure created_at defaults
            migrationBuilder.Sql(@"
                ALTER TABLE evaluation_state ALTER COLUMN created_at SET DEFAULT NOW();
                ALTER TABLE approval_levels ALTER COLUMN created_at SET DEFAULT NOW();
                ALTER TABLE approval_workflows ALTER COLUMN created_at SET DEFAULT NOW();
            ");

            // 7. bidders: add activation fields
            migrationBuilder.Sql(@"
                ALTER TABLE bidders ADD COLUMN IF NOT EXISTS activation_token varchar(500);
                ALTER TABLE bidders ADD COLUMN IF NOT EXISTS activation_token_expiry TIMESTAMP WITH TIME ZONE;
            ");

            // 8. notification_preferences: add missing columns
            migrationBuilder.Sql(@"
                ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS addendum_issued boolean NOT NULL DEFAULT true;
                ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS approval_request boolean NOT NULL DEFAULT true;
                ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS clarification_published boolean NOT NULL DEFAULT true;
                ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS deadline_reminder_1day boolean NOT NULL DEFAULT true;
                ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS deadline_reminder_3days boolean NOT NULL DEFAULT true;
                ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS tender_invitation boolean NOT NULL DEFAULT true;
            ");

            // 9. Recreate technical_scores if schema has bid_submission_id instead of tender_id
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='technical_scores' AND column_name='bid_submission_id') THEN
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
                    CREATE UNIQUE INDEX ""IX_technical_scores_tender_bidder_panelist_criterion"" ON technical_scores (tender_id, bidder_id, panelist_user_id, criterion_id);
                    CREATE INDEX ""IX_technical_scores_tender_id"" ON technical_scores (tender_id);
                    CREATE INDEX ""IX_technical_scores_tender_bidder"" ON technical_scores (tender_id, bidder_id);
                  END IF;
                END $$;
            ");

            // 10. Recreate commercial_scores if schema is wrong
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='commercial_scores' AND column_name='bid_submission_id') THEN
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
                    CREATE UNIQUE INDEX ""IX_commercial_scores_tender_bidder"" ON commercial_scores (tender_id, bidder_id);
                  END IF;
                END $$;
            ");

            // 11. Recreate combined_scorecards if schema is wrong
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='combined_scorecards' AND column_name='bid_submission_id') THEN
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
                    CREATE UNIQUE INDEX ""IX_combined_scorecards_tender_bidder"" ON combined_scorecards (tender_id, bidder_id);
                  END IF;
                END $$;
            ");

            // 12. clarification_bulletins: add missing columns + fix constraints
            migrationBuilder.Sql(@"
                ALTER TABLE clarification_bulletins ADD COLUMN IF NOT EXISTS issue_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
                ALTER TABLE clarification_bulletins ADD COLUMN IF NOT EXISTS introduction TEXT;
                ALTER TABLE clarification_bulletins ADD COLUMN IF NOT EXISTS closing_notes TEXT;
                ALTER TABLE clarification_bulletins ALTER COLUMN created_at SET DEFAULT NOW();
                ALTER TABLE clarification_bulletins ALTER COLUMN published_at SET DEFAULT NOW();
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clarification_bulletins' AND column_name='title' AND is_nullable='NO') THEN
                    ALTER TABLE clarification_bulletins ALTER COLUMN title DROP NOT NULL;
                    ALTER TABLE clarification_bulletins ALTER COLUMN title SET DEFAULT '';
                  END IF;
                END $$;
            ");

            // 13. audit_logs: widen columns + drop FK + make user_id nullable
            migrationBuilder.Sql(@"
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='action' AND character_maximum_length < 500) THEN
                    ALTER TABLE audit_logs ALTER COLUMN action TYPE VARCHAR(500);
                  END IF;
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='entity_type' AND character_maximum_length < 500) THEN
                    ALTER TABLE audit_logs ALTER COLUMN entity_type TYPE VARCHAR(500);
                  END IF;
                END $$;
                ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS ""FK_audit_logs_users_user_id"";
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_logs' AND column_name='user_id' AND is_nullable='NO') THEN
                    ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;
                  END IF;
                END $$;
            ");

            // 14. vendor_pricing_snapshots: add missing columns + fix nullable
            migrationBuilder.Sql(@"
                ALTER TABLE vendor_pricing_snapshots ADD COLUMN IF NOT EXISTS bidder_id UUID;
                ALTER TABLE vendor_pricing_snapshots ADD COLUMN IF NOT EXISTS bid_submission_id UUID;
                ALTER TABLE vendor_pricing_snapshots ADD COLUMN IF NOT EXISTS tender_base_currency VARCHAR(10) NOT NULL DEFAULT 'SAR';
                ALTER TABLE vendor_pricing_snapshots ADD COLUMN IF NOT EXISTS total_bid_amount NUMERIC(18,2) NOT NULL DEFAULT 0;
                ALTER TABLE vendor_pricing_snapshots ADD COLUMN IF NOT EXISTS total_items_count INTEGER NOT NULL DEFAULT 0;
                DO $$ BEGIN
                  IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='FK_vendor_pricing_snapshots_bidders_bidder_id') THEN
                    BEGIN
                      ALTER TABLE vendor_pricing_snapshots ADD CONSTRAINT ""FK_vendor_pricing_snapshots_bidders_bidder_id"" FOREIGN KEY (bidder_id) REFERENCES bidders(id) ON DELETE RESTRICT;
                    EXCEPTION WHEN OTHERS THEN NULL;
                    END;
                  END IF;
                END $$;
                CREATE INDEX IF NOT EXISTS ""IX_vendor_pricing_snapshots_bidder_id"" ON vendor_pricing_snapshots (bidder_id);
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vendor_pricing_snapshots' AND column_name='created_by' AND is_nullable='NO') THEN
                    ALTER TABLE vendor_pricing_snapshots ALTER COLUMN created_by DROP NOT NULL;
                  END IF;
                END $$;
            ");

            // 15. vendor_item_rates: add missing columns + fix nullable + defaults
            migrationBuilder.Sql(@"
                ALTER TABLE vendor_item_rates ADD COLUMN IF NOT EXISTS bidder_id UUID;
                ALTER TABLE vendor_item_rates ADD COLUMN IF NOT EXISTS tender_id UUID;
                ALTER TABLE vendor_item_rates ADD COLUMN IF NOT EXISTS item_description TEXT NOT NULL DEFAULT '';
                ALTER TABLE vendor_item_rates ADD COLUMN IF NOT EXISTS uom VARCHAR(50) NOT NULL DEFAULT '';
                ALTER TABLE vendor_item_rates ADD COLUMN IF NOT EXISTS quantity NUMERIC(18,4) NOT NULL DEFAULT 0;
                ALTER TABLE vendor_item_rates ADD COLUMN IF NOT EXISTS unit_rate NUMERIC(18,4) NOT NULL DEFAULT 0;
                ALTER TABLE vendor_item_rates ADD COLUMN IF NOT EXISTS total_amount NUMERIC(18,2) NOT NULL DEFAULT 0;
                ALTER TABLE vendor_item_rates ADD COLUMN IF NOT EXISTS normalized_currency VARCHAR(3) NOT NULL DEFAULT 'SAR';
                ALTER TABLE vendor_item_rates ALTER COLUMN rank SET DEFAULT 0;
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vendor_item_rates' AND column_name='boq_item_id' AND is_nullable='NO') THEN
                    ALTER TABLE vendor_item_rates ALTER COLUMN boq_item_id DROP NOT NULL;
                  END IF;
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vendor_item_rates' AND column_name='currency')
                     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vendor_item_rates' AND column_name='normalized_currency') THEN
                    ALTER TABLE vendor_item_rates RENAME COLUMN currency TO normalized_currency;
                  END IF;
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vendor_item_rates' AND column_name='bid_submission_id' AND is_nullable='NO') THEN
                    ALTER TABLE vendor_item_rates ALTER COLUMN bid_submission_id DROP NOT NULL;
                  END IF;
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vendor_item_rates' AND column_name='bidder_id' AND is_nullable='NO') THEN
                    ALTER TABLE vendor_item_rates ALTER COLUMN bidder_id DROP NOT NULL;
                  END IF;
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vendor_item_rates' AND column_name='tender_id' AND is_nullable='NO') THEN
                    ALTER TABLE vendor_item_rates ALTER COLUMN tender_id DROP NOT NULL;
                  END IF;
                END $$;
            ");

            // 16. addendum_acknowledgments: add missing columns + fix nullable
            migrationBuilder.Sql(@"
                ALTER TABLE addendum_acknowledgments ADD COLUMN IF NOT EXISTS email_sent_at TIMESTAMP WITH TIME ZONE;
                ALTER TABLE addendum_acknowledgments ADD COLUMN IF NOT EXISTS email_opened_at TIMESTAMP WITH TIME ZONE;
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='addendum_acknowledgments' AND column_name='acknowledged_at' AND is_nullable='NO') THEN
                    ALTER TABLE addendum_acknowledgments ALTER COLUMN acknowledged_at DROP NOT NULL;
                  END IF;
                END $$;
            ");
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            // Down migration is intentionally minimal — these are fixes to align
            // the database with entity configurations, not new features.
            // Reverting would break the application.
            migrationBuilder.Sql("-- ConsolidateSchemaFixes: Down migration intentionally empty (alignment fixes)");
        }
    }
}
