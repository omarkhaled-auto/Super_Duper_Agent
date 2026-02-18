using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Bayan.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddHierarchicalBoqSupport : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "bidders",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    company_name = table.Column<string>(type: "character varying(300)", maxLength: 300, nullable: false),
                    cr_number = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    license_number = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    contact_person = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    email = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: false),
                    phone = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    trade_specialization = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    prequalification_status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Pending'"),
                    company_profile_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    password_hash = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    last_login_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    activation_token = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    activation_token_expiry = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_bidders", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "clients",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    name = table.Column<string>(type: "character varying(300)", maxLength: 300, nullable: false),
                    contact_person = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    email = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                    phone = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    address = table.Column<string>(type: "text", nullable: true),
                    city = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    country = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    cr_number = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    vat_number = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    contact_email = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                    contact_phone = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_clients", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "system_settings",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    key = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    value = table.Column<string>(type: "text", nullable: false),
                    description = table.Column<string>(type: "text", nullable: true),
                    data_type = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValue: "string"),
                    category = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    is_editable = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    display_order = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                    created_by = table.Column<Guid>(type: "uuid", nullable: true),
                    last_modified_by = table.Column<Guid>(type: "uuid", nullable: true),
                    last_modified_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_system_settings", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "units_of_measure",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    conversion_factor = table.Column<decimal>(type: "numeric(18,6)", precision: 18, scale: 6, nullable: false, defaultValue: 1.0m),
                    base_unit_code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    display_order = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                    created_by = table.Column<Guid>(type: "uuid", nullable: true),
                    last_modified_by = table.Column<Guid>(type: "uuid", nullable: true),
                    last_modified_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_units_of_measure", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "uom_master",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    category = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    base_unit_code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    conversion_to_base = table.Column<decimal>(type: "numeric(18,10)", precision: 18, scale: 10, nullable: true),
                    is_system = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_uom_master", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "users",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    email = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: false),
                    password_hash = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    first_name = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    last_name = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    phone = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    role = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    email_verified = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    email_verification_token = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    email_verification_token_expiry = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    password_reset_token = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    password_reset_token_expiry = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    last_login_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    failed_login_attempts = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                    lockout_end = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    refresh_token = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    refresh_token_expiry = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    company_name = table.Column<string>(type: "character varying(300)", maxLength: 300, nullable: true),
                    commercial_registration_number = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    department = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    job_title = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    profile_picture_url = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    preferred_language = table.Column<string>(type: "character varying(10)", maxLength: 10, nullable: false, defaultValue: "ar"),
                    timezone = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValue: "Asia/Riyadh"),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_users", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "bidder_refresh_tokens",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    token = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    expires_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    is_revoked = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    revoked_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_by_ip = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    revoked_by_ip = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    replaced_by_token = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_bidder_refresh_tokens", x => x.id);
                    table.ForeignKey(
                        name: "FK_bidder_refresh_tokens_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "audit_logs",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    user_id = table.Column<Guid>(type: "uuid", nullable: true),
                    user_email = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                    action = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    entity_type = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    entity_id = table.Column<Guid>(type: "uuid", nullable: true),
                    old_values = table.Column<string>(type: "jsonb", nullable: true),
                    new_values = table.Column<string>(type: "jsonb", nullable: true),
                    ip_address = table.Column<string>(type: "character varying(45)", maxLength: 45, nullable: true),
                    user_agent = table.Column<string>(type: "text", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_audit_logs", x => x.id);
                    table.ForeignKey(
                        name: "FK_audit_logs_users_user_id",
                        column: x => x.user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "notification_preferences",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_invitation = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    addendum_issued = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    clarification_published = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    deadline_reminder_3days = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    deadline_reminder_1day = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    approval_request = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_notification_preferences", x => x.id);
                    table.ForeignKey(
                        name: "FK_notification_preferences_users_user_id",
                        column: x => x.user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "refresh_tokens",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    token = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    expires_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    is_revoked = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    revoked_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_by_ip = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    revoked_by_ip = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    replaced_by_token = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_refresh_tokens", x => x.id);
                    table.ForeignKey(
                        name: "FK_refresh_tokens_users_user_id",
                        column: x => x.user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "tenders",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    title = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    reference = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    description = table.Column<string>(type: "character varying(4000)", maxLength: 4000, nullable: true),
                    client_id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_type = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    base_currency = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false, defaultValue: "AED"),
                    estimated_value = table.Column<decimal>(type: "numeric(18,2)", nullable: true),
                    bid_validity_days = table.Column<int>(type: "integer", nullable: false, defaultValue: 90),
                    issue_date = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    clarification_deadline = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    submission_deadline = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    opening_date = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    technical_weight = table.Column<int>(type: "integer", nullable: false, defaultValue: 40),
                    commercial_weight = table.Column<int>(type: "integer", nullable: false, defaultValue: 60),
                    pricing_level = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false, defaultValueSql: "'SubItem'"),
                    status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Draft'"),
                    published_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    awarded_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_by = table.Column<Guid>(type: "uuid", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tenders", x => x.id);
                    table.ForeignKey(
                        name: "FK_tenders_clients_client_id",
                        column: x => x.client_id,
                        principalTable: "clients",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tenders_users_created_by",
                        column: x => x.created_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "addenda",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    addendum_number = table.Column<int>(type: "integer", nullable: false),
                    issue_date = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    summary = table.Column<string>(type: "text", nullable: false),
                    extends_deadline = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    new_deadline = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Draft'"),
                    issued_by = table.Column<Guid>(type: "uuid", nullable: true),
                    issued_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_addenda", x => x.id);
                    table.ForeignKey(
                        name: "FK_addenda_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_addenda_users_issued_by",
                        column: x => x.issued_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "approval_workflows",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Pending'"),
                    initiated_by = table.Column<Guid>(type: "uuid", nullable: false),
                    initiated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    completed_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    award_pack_pdf_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_approval_workflows", x => x.id);
                    table.ForeignKey(
                        name: "FK_approval_workflows_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_approval_workflows_users_initiated_by",
                        column: x => x.initiated_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "bid_exceptions",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    exception_type = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    description = table.Column<string>(type: "text", nullable: false),
                    cost_impact = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: true),
                    time_impact_days = table.Column<int>(type: "integer", nullable: true),
                    risk_level = table.Column<string>(type: "character varying(10)", maxLength: 10, nullable: false),
                    mitigation = table.Column<string>(type: "text", nullable: true),
                    logged_by = table.Column<Guid>(type: "uuid", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_bid_exceptions", x => x.id);
                    table.ForeignKey(
                        name: "FK_bid_exceptions_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_bid_exceptions_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_bid_exceptions_users_logged_by",
                        column: x => x.logged_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "bid_submissions",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    submission_time = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    is_late = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    late_accepted = table.Column<bool>(type: "boolean", nullable: true),
                    late_accepted_by = table.Column<Guid>(type: "uuid", nullable: true),
                    original_file_name = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    original_file_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    native_currency = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false, defaultValue: "AED"),
                    native_total_amount = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: true),
                    fx_rate = table.Column<decimal>(type: "numeric(10,6)", precision: 10, scale: 6, nullable: false, defaultValue: 1.0m),
                    normalized_total_amount = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: true),
                    bid_validity_days = table.Column<int>(type: "integer", nullable: false, defaultValue: 90),
                    import_status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Uploaded'"),
                    import_started_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    import_completed_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    imported_by = table.Column<Guid>(type: "uuid", nullable: true),
                    validation_summary = table.Column<string>(type: "jsonb", nullable: true),
                    receipt_number = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    receipt_pdf_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Submitted'"),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_bid_submissions", x => x.id);
                    table.ForeignKey(
                        name: "FK_bid_submissions_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_bid_submissions_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_bid_submissions_users_imported_by",
                        column: x => x.imported_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_bid_submissions_users_late_accepted_by",
                        column: x => x.late_accepted_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "boq_sections",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    parent_section_id = table.Column<Guid>(type: "uuid", nullable: true),
                    section_number = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    title = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    sort_order = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_boq_sections", x => x.id);
                    table.ForeignKey(
                        name: "FK_boq_sections_boq_sections_parent_section_id",
                        column: x => x.parent_section_id,
                        principalTable: "boq_sections",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_boq_sections_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "clarification_bulletins",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bulletin_number = table.Column<int>(type: "integer", nullable: false),
                    issue_date = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    introduction = table.Column<string>(type: "text", nullable: true),
                    closing_notes = table.Column<string>(type: "text", nullable: true),
                    pdf_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    published_by = table.Column<Guid>(type: "uuid", nullable: false),
                    published_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_clarification_bulletins", x => x.id);
                    table.ForeignKey(
                        name: "FK_clarification_bulletins_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_clarification_bulletins_users_published_by",
                        column: x => x.published_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "combined_scorecards",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    technical_score_avg = table.Column<decimal>(type: "numeric(6,2)", precision: 6, scale: 2, nullable: false),
                    technical_rank = table.Column<int>(type: "integer", nullable: false),
                    commercial_score = table.Column<decimal>(type: "numeric(6,2)", precision: 6, scale: 2, nullable: false),
                    commercial_rank = table.Column<int>(type: "integer", nullable: false),
                    technical_weight = table.Column<int>(type: "integer", nullable: false),
                    commercial_weight = table.Column<int>(type: "integer", nullable: false),
                    combined_score = table.Column<decimal>(type: "numeric(6,2)", precision: 6, scale: 2, nullable: false),
                    final_rank = table.Column<int>(type: "integer", nullable: false),
                    is_recommended = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    calculated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_combined_scorecards", x => x.id);
                    table.ForeignKey(
                        name: "FK_combined_scorecards_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_combined_scorecards_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "commercial_scores",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    normalized_total_price = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: false),
                    commercial_score = table.Column<decimal>(type: "numeric(6,2)", precision: 6, scale: 2, nullable: false),
                    rank = table.Column<int>(type: "integer", nullable: false),
                    include_provisional_sums = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    include_alternates = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    calculated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_commercial_scores", x => x.id);
                    table.ForeignKey(
                        name: "FK_commercial_scores_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_commercial_scores_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "documents",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    folder_path = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    file_name = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    file_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: false),
                    file_size_bytes = table.Column<long>(type: "bigint", nullable: false),
                    content_type = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    version = table.Column<int>(type: "integer", nullable: false, defaultValue: 1),
                    is_latest = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    uploaded_by = table.Column<Guid>(type: "uuid", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_documents", x => x.id);
                    table.ForeignKey(
                        name: "FK_documents_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_documents_users_uploaded_by",
                        column: x => x.uploaded_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "email_logs",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: true),
                    recipient_email = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: false),
                    recipient_name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    email_type = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    subject = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    body = table.Column<string>(type: "text", nullable: true),
                    status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Pending'"),
                    sent_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    error_message = table.Column<string>(type: "text", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_email_logs", x => x.id);
                    table.ForeignKey(
                        name: "FK_email_logs_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "evaluation_criteria",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    weight_percentage = table.Column<decimal>(type: "numeric(5,2)", precision: 5, scale: 2, nullable: false),
                    guidance_notes = table.Column<string>(type: "text", nullable: true),
                    sort_order = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_evaluation_criteria", x => x.id);
                    table.ForeignKey(
                        name: "FK_evaluation_criteria_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "evaluation_panels",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    panelist_user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    assigned_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    completed_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_evaluation_panels", x => x.id);
                    table.ForeignKey(
                        name: "FK_evaluation_panels_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_evaluation_panels_users_panelist_user_id",
                        column: x => x.panelist_user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "evaluation_state",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    scoring_method = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false, defaultValueSql: "'Numeric'"),
                    blind_mode = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    technical_evaluation_deadline = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    technical_scores_locked = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    technical_locked_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    technical_locked_by = table.Column<Guid>(type: "uuid", nullable: true),
                    commercial_scores_calculated = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    combined_scores_calculated = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_evaluation_state", x => x.id);
                    table.ForeignKey(
                        name: "FK_evaluation_state_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_evaluation_state_users_technical_locked_by",
                        column: x => x.technical_locked_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "tender_bidders",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    invitation_sent_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    invitation_opened_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    registered_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    nda_status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Pending'"),
                    nda_document_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    nda_signed_date = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    nda_expiry_date = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    qualification_status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Pending'"),
                    qualified_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    qualification_reason = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_tender_bidders", x => x.id);
                    table.ForeignKey(
                        name: "FK_tender_bidders_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_tender_bidders_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "addendum_acknowledgments",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    addendum_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    email_sent_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    email_opened_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    acknowledged_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_addendum_acknowledgments", x => x.id);
                    table.ForeignKey(
                        name: "FK_addendum_acknowledgments_addenda_addendum_id",
                        column: x => x.addendum_id,
                        principalTable: "addenda",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_addendum_acknowledgments_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "approval_levels",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    workflow_id = table.Column<Guid>(type: "uuid", nullable: false),
                    level_number = table.Column<int>(type: "integer", nullable: false),
                    approver_user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    deadline = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    decision = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    decision_comment = table.Column<string>(type: "text", nullable: true),
                    decided_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Waiting'"),
                    notified_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_approval_levels", x => x.id);
                    table.ForeignKey(
                        name: "FK_approval_levels_approval_workflows_workflow_id",
                        column: x => x.workflow_id,
                        principalTable: "approval_workflows",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_approval_levels_users_approver_user_id",
                        column: x => x.approver_user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "bid_documents",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    bid_submission_id = table.Column<Guid>(type: "uuid", nullable: false),
                    document_type = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    file_name = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    file_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: false),
                    file_size_bytes = table.Column<long>(type: "bigint", nullable: false),
                    content_type = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    uploaded_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_bid_documents", x => x.id);
                    table.ForeignKey(
                        name: "FK_bid_documents_bid_submissions_bid_submission_id",
                        column: x => x.bid_submission_id,
                        principalTable: "bid_submissions",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "vendor_pricing_snapshots",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bid_submission_id = table.Column<Guid>(type: "uuid", nullable: false),
                    snapshot_date = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    tender_base_currency = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    total_bid_amount = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: false),
                    total_items_count = table.Column<int>(type: "integer", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_vendor_pricing_snapshots", x => x.id);
                    table.ForeignKey(
                        name: "FK_vendor_pricing_snapshots_bid_submissions_bid_submission_id",
                        column: x => x.bid_submission_id,
                        principalTable: "bid_submissions",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_vendor_pricing_snapshots_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_vendor_pricing_snapshots_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "boq_items",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    section_id = table.Column<Guid>(type: "uuid", nullable: false),
                    item_number = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    description = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: false),
                    quantity = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: false),
                    uom = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    item_type = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Base'"),
                    notes = table.Column<string>(type: "text", nullable: true),
                    sort_order = table.Column<int>(type: "integer", nullable: false, defaultValue: 0),
                    parent_item_id = table.Column<Guid>(type: "uuid", nullable: true),
                    is_group = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_boq_items", x => x.id);
                    table.ForeignKey(
                        name: "FK_boq_items_boq_items_parent_item_id",
                        column: x => x.parent_item_id,
                        principalTable: "boq_items",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_boq_items_boq_sections_section_id",
                        column: x => x.section_id,
                        principalTable: "boq_sections",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_boq_items_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "clarifications",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    reference_number = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    subject = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    question = table.Column<string>(type: "text", nullable: false),
                    submitted_by_bidder_id = table.Column<Guid>(type: "uuid", nullable: true),
                    submitted_by_user_id = table.Column<Guid>(type: "uuid", nullable: true),
                    related_boq_section = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    related_document_id = table.Column<Guid>(type: "uuid", nullable: true),
                    is_anonymous = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    priority = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false, defaultValueSql: "'Normal'"),
                    answer = table.Column<string>(type: "text", nullable: true),
                    answered_by = table.Column<Guid>(type: "uuid", nullable: true),
                    answered_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    assigned_to_id = table.Column<Guid>(type: "uuid", nullable: true),
                    clarification_type = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'BidderQuestion'"),
                    status = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false, defaultValueSql: "'Submitted'"),
                    duplicate_of_id = table.Column<Guid>(type: "uuid", nullable: true),
                    published_in_bulletin_id = table.Column<Guid>(type: "uuid", nullable: true),
                    published_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    submitted_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_clarifications", x => x.id);
                    table.ForeignKey(
                        name: "FK_clarifications_bidders_submitted_by_bidder_id",
                        column: x => x.submitted_by_bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_clarifications_clarification_bulletins_published_in_bulleti~",
                        column: x => x.published_in_bulletin_id,
                        principalTable: "clarification_bulletins",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_clarifications_clarifications_duplicate_of_id",
                        column: x => x.duplicate_of_id,
                        principalTable: "clarifications",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_clarifications_documents_related_document_id",
                        column: x => x.related_document_id,
                        principalTable: "documents",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_clarifications_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_clarifications_users_answered_by",
                        column: x => x.answered_by,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_clarifications_users_assigned_to_id",
                        column: x => x.assigned_to_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_clarifications_users_submitted_by_user_id",
                        column: x => x.submitted_by_user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "technical_scores",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    tender_id = table.Column<Guid>(type: "uuid", nullable: false),
                    bidder_id = table.Column<Guid>(type: "uuid", nullable: false),
                    panelist_user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    criterion_id = table.Column<Guid>(type: "uuid", nullable: false),
                    score = table.Column<decimal>(type: "numeric(4,1)", precision: 4, scale: 1, nullable: false),
                    comment = table.Column<string>(type: "text", nullable: true),
                    is_draft = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    submitted_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_technical_scores", x => x.id);
                    table.ForeignKey(
                        name: "FK_technical_scores_bidders_bidder_id",
                        column: x => x.bidder_id,
                        principalTable: "bidders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_technical_scores_evaluation_criteria_criterion_id",
                        column: x => x.criterion_id,
                        principalTable: "evaluation_criteria",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_technical_scores_tenders_tender_id",
                        column: x => x.tender_id,
                        principalTable: "tenders",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_technical_scores_users_panelist_user_id",
                        column: x => x.panelist_user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "bid_pricing",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    bid_submission_id = table.Column<Guid>(type: "uuid", nullable: false),
                    boq_item_id = table.Column<Guid>(type: "uuid", nullable: true),
                    bidder_item_number = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    bidder_description = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    bidder_quantity = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: true),
                    bidder_uom = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    native_unit_rate = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: true),
                    native_amount = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: true),
                    native_currency = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    normalized_unit_rate = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: true),
                    normalized_amount = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: true),
                    fx_rate_applied = table.Column<decimal>(type: "numeric(10,6)", precision: 10, scale: 6, nullable: true),
                    uom_conversion_factor = table.Column<decimal>(type: "numeric(18,10)", precision: 18, scale: 10, nullable: true),
                    match_type = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    match_confidence = table.Column<decimal>(type: "numeric(5,2)", precision: 5, scale: 2, nullable: true),
                    is_included_in_total = table.Column<bool>(type: "boolean", nullable: false, defaultValue: true),
                    is_outlier = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    outlier_severity = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: true),
                    deviation_from_average = table.Column<decimal>(type: "numeric(10,4)", precision: 10, scale: 4, nullable: true),
                    has_formula_error = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    is_no_bid = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    is_non_comparable = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    notes = table.Column<string>(type: "text", nullable: true),
                    boq_section_id = table.Column<Guid>(type: "uuid", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_bid_pricing", x => x.id);
                    table.ForeignKey(
                        name: "FK_bid_pricing_bid_submissions_bid_submission_id",
                        column: x => x.bid_submission_id,
                        principalTable: "bid_submissions",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_bid_pricing_boq_items_boq_item_id",
                        column: x => x.boq_item_id,
                        principalTable: "boq_items",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_bid_pricing_boq_sections_boq_section_id",
                        column: x => x.boq_section_id,
                        principalTable: "boq_sections",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "vendor_item_rates",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    snapshot_id = table.Column<Guid>(type: "uuid", nullable: false),
                    boq_item_id = table.Column<Guid>(type: "uuid", nullable: true),
                    item_description = table.Column<string>(type: "text", nullable: false),
                    uom = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    normalized_unit_rate = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: false),
                    normalized_currency = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    quantity = table.Column<decimal>(type: "numeric(18,4)", precision: 18, scale: 4, nullable: true),
                    total_amount = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_vendor_item_rates", x => x.id);
                    table.ForeignKey(
                        name: "FK_vendor_item_rates_boq_items_boq_item_id",
                        column: x => x.boq_item_id,
                        principalTable: "boq_items",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_vendor_item_rates_vendor_pricing_snapshots_snapshot_id",
                        column: x => x.snapshot_id,
                        principalTable: "vendor_pricing_snapshots",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "clarification_attachments",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    clarification_id = table.Column<Guid>(type: "uuid", nullable: false),
                    file_name = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: false),
                    file_path = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: false),
                    file_size_bytes = table.Column<long>(type: "bigint", nullable: false),
                    content_type = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    uploaded_by_user_id = table.Column<Guid>(type: "uuid", nullable: true),
                    created_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    updated_at = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_clarification_attachments", x => x.id);
                    table.ForeignKey(
                        name: "FK_clarification_attachments_clarifications_clarification_id",
                        column: x => x.clarification_id,
                        principalTable: "clarifications",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_clarification_attachments_users_uploaded_by_user_id",
                        column: x => x.uploaded_by_user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_addenda_issued_by",
                table: "addenda",
                column: "issued_by");

            migrationBuilder.CreateIndex(
                name: "IX_addenda_tender_id_addendum_number",
                table: "addenda",
                columns: new[] { "tender_id", "addendum_number" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_addendum_acknowledgments_addendum_id_bidder_id",
                table: "addendum_acknowledgments",
                columns: new[] { "addendum_id", "bidder_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_addendum_acknowledgments_bidder_id",
                table: "addendum_acknowledgments",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_approval_levels_approver_user_id",
                table: "approval_levels",
                column: "approver_user_id");

            migrationBuilder.CreateIndex(
                name: "IX_approval_levels_workflow_id_level_number",
                table: "approval_levels",
                columns: new[] { "workflow_id", "level_number" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_approval_workflows_initiated_by",
                table: "approval_workflows",
                column: "initiated_by");

            migrationBuilder.CreateIndex(
                name: "IX_approval_workflows_tender_id",
                table: "approval_workflows",
                column: "tender_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_audit_logs_action",
                table: "audit_logs",
                column: "action");

            migrationBuilder.CreateIndex(
                name: "IX_audit_logs_created_at",
                table: "audit_logs",
                column: "created_at");

            migrationBuilder.CreateIndex(
                name: "IX_audit_logs_entity_type_entity_id",
                table: "audit_logs",
                columns: new[] { "entity_type", "entity_id" });

            migrationBuilder.CreateIndex(
                name: "IX_audit_logs_user_id",
                table: "audit_logs",
                column: "user_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_documents_bid_submission_id",
                table: "bid_documents",
                column: "bid_submission_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_exceptions_bidder_id",
                table: "bid_exceptions",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_exceptions_logged_by",
                table: "bid_exceptions",
                column: "logged_by");

            migrationBuilder.CreateIndex(
                name: "IX_bid_exceptions_tender_id",
                table: "bid_exceptions",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_pricing_bid_submission_id",
                table: "bid_pricing",
                column: "bid_submission_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_pricing_bid_submission_id_is_outlier",
                table: "bid_pricing",
                columns: new[] { "bid_submission_id", "is_outlier" });

            migrationBuilder.CreateIndex(
                name: "IX_bid_pricing_boq_item_id",
                table: "bid_pricing",
                column: "boq_item_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_pricing_boq_section_id",
                table: "bid_pricing",
                column: "boq_section_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_submissions_bidder_id",
                table: "bid_submissions",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_submissions_imported_by",
                table: "bid_submissions",
                column: "imported_by");

            migrationBuilder.CreateIndex(
                name: "IX_bid_submissions_late_accepted_by",
                table: "bid_submissions",
                column: "late_accepted_by");

            migrationBuilder.CreateIndex(
                name: "IX_bid_submissions_receipt_number",
                table: "bid_submissions",
                column: "receipt_number",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_bid_submissions_tender_id",
                table: "bid_submissions",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_bid_submissions_tender_id_bidder_id",
                table: "bid_submissions",
                columns: new[] { "tender_id", "bidder_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_bidder_refresh_tokens_bidder_id",
                table: "bidder_refresh_tokens",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_bidder_refresh_tokens_token",
                table: "bidder_refresh_tokens",
                column: "token",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_bidders_email",
                table: "bidders",
                column: "email");

            migrationBuilder.CreateIndex(
                name: "IX_bidders_trade_specialization",
                table: "bidders",
                column: "trade_specialization");

            migrationBuilder.CreateIndex(
                name: "IX_boq_items_parent_item_id",
                table: "boq_items",
                column: "parent_item_id");

            migrationBuilder.CreateIndex(
                name: "IX_boq_items_section_id",
                table: "boq_items",
                column: "section_id");

            migrationBuilder.CreateIndex(
                name: "IX_boq_items_tender_id",
                table: "boq_items",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_boq_items_tender_id_item_number",
                table: "boq_items",
                columns: new[] { "tender_id", "item_number" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_boq_sections_parent_section_id",
                table: "boq_sections",
                column: "parent_section_id");

            migrationBuilder.CreateIndex(
                name: "IX_boq_sections_tender_id",
                table: "boq_sections",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarification_attachments_clarification_id",
                table: "clarification_attachments",
                column: "clarification_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarification_attachments_uploaded_by_user_id",
                table: "clarification_attachments",
                column: "uploaded_by_user_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarification_bulletins_published_by",
                table: "clarification_bulletins",
                column: "published_by");

            migrationBuilder.CreateIndex(
                name: "IX_clarification_bulletins_tender_id_bulletin_number",
                table: "clarification_bulletins",
                columns: new[] { "tender_id", "bulletin_number" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_answered_by",
                table: "clarifications",
                column: "answered_by");

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_assigned_to_id",
                table: "clarifications",
                column: "assigned_to_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_duplicate_of_id",
                table: "clarifications",
                column: "duplicate_of_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_published_in_bulletin_id",
                table: "clarifications",
                column: "published_in_bulletin_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_related_document_id",
                table: "clarifications",
                column: "related_document_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_submitted_by_bidder_id",
                table: "clarifications",
                column: "submitted_by_bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_submitted_by_user_id",
                table: "clarifications",
                column: "submitted_by_user_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_tender_id",
                table: "clarifications",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_tender_id_reference_number",
                table: "clarifications",
                columns: new[] { "tender_id", "reference_number" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_clarifications_tender_id_status",
                table: "clarifications",
                columns: new[] { "tender_id", "status" });

            migrationBuilder.CreateIndex(
                name: "IX_combined_scorecards_bidder_id",
                table: "combined_scorecards",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_combined_scorecards_tender_id_bidder_id",
                table: "combined_scorecards",
                columns: new[] { "tender_id", "bidder_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_commercial_scores_bidder_id",
                table: "commercial_scores",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_commercial_scores_tender_id_bidder_id",
                table: "commercial_scores",
                columns: new[] { "tender_id", "bidder_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_documents_tender_id",
                table: "documents",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_documents_tender_id_folder_path",
                table: "documents",
                columns: new[] { "tender_id", "folder_path" });

            migrationBuilder.CreateIndex(
                name: "IX_documents_uploaded_by",
                table: "documents",
                column: "uploaded_by");

            migrationBuilder.CreateIndex(
                name: "IX_email_logs_tender_id",
                table: "email_logs",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_evaluation_criteria_tender_id",
                table: "evaluation_criteria",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_evaluation_panels_panelist_user_id",
                table: "evaluation_panels",
                column: "panelist_user_id");

            migrationBuilder.CreateIndex(
                name: "IX_evaluation_panels_tender_id_panelist_user_id",
                table: "evaluation_panels",
                columns: new[] { "tender_id", "panelist_user_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_evaluation_state_technical_locked_by",
                table: "evaluation_state",
                column: "technical_locked_by");

            migrationBuilder.CreateIndex(
                name: "IX_evaluation_state_tender_id",
                table: "evaluation_state",
                column: "tender_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_notification_preferences_user_id",
                table: "notification_preferences",
                column: "user_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_refresh_tokens_token",
                table: "refresh_tokens",
                column: "token",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_refresh_tokens_user_id",
                table: "refresh_tokens",
                column: "user_id");

            migrationBuilder.CreateIndex(
                name: "IX_system_settings_key",
                table: "system_settings",
                column: "key",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_technical_scores_bidder_id",
                table: "technical_scores",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_technical_scores_criterion_id",
                table: "technical_scores",
                column: "criterion_id");

            migrationBuilder.CreateIndex(
                name: "IX_technical_scores_panelist_user_id",
                table: "technical_scores",
                column: "panelist_user_id");

            migrationBuilder.CreateIndex(
                name: "IX_technical_scores_tender_id",
                table: "technical_scores",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_technical_scores_tender_id_bidder_id",
                table: "technical_scores",
                columns: new[] { "tender_id", "bidder_id" });

            migrationBuilder.CreateIndex(
                name: "IX_technical_scores_tender_id_bidder_id_panelist_user_id_crite~",
                table: "technical_scores",
                columns: new[] { "tender_id", "bidder_id", "panelist_user_id", "criterion_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tender_bidders_bidder_id",
                table: "tender_bidders",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_tender_bidders_tender_id",
                table: "tender_bidders",
                column: "tender_id");

            migrationBuilder.CreateIndex(
                name: "IX_tender_bidders_tender_id_bidder_id",
                table: "tender_bidders",
                columns: new[] { "tender_id", "bidder_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tenders_client_id",
                table: "tenders",
                column: "client_id");

            migrationBuilder.CreateIndex(
                name: "IX_tenders_created_by",
                table: "tenders",
                column: "created_by");

            migrationBuilder.CreateIndex(
                name: "IX_tenders_reference",
                table: "tenders",
                column: "reference",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_tenders_status",
                table: "tenders",
                column: "status");

            migrationBuilder.CreateIndex(
                name: "IX_tenders_submission_deadline",
                table: "tenders",
                column: "submission_deadline");

            migrationBuilder.CreateIndex(
                name: "IX_units_of_measure_code",
                table: "units_of_measure",
                column: "code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_uom_master_code",
                table: "uom_master",
                column: "code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_users_email",
                table: "users",
                column: "email",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_vendor_item_rates_boq_item_id",
                table: "vendor_item_rates",
                column: "boq_item_id");

            migrationBuilder.CreateIndex(
                name: "IX_vendor_item_rates_snapshot_id",
                table: "vendor_item_rates",
                column: "snapshot_id");

            migrationBuilder.CreateIndex(
                name: "IX_vendor_pricing_snapshots_bid_submission_id",
                table: "vendor_pricing_snapshots",
                column: "bid_submission_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_vendor_pricing_snapshots_bidder_id",
                table: "vendor_pricing_snapshots",
                column: "bidder_id");

            migrationBuilder.CreateIndex(
                name: "IX_vendor_pricing_snapshots_tender_id",
                table: "vendor_pricing_snapshots",
                column: "tender_id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "addendum_acknowledgments");

            migrationBuilder.DropTable(
                name: "approval_levels");

            migrationBuilder.DropTable(
                name: "audit_logs");

            migrationBuilder.DropTable(
                name: "bid_documents");

            migrationBuilder.DropTable(
                name: "bid_exceptions");

            migrationBuilder.DropTable(
                name: "bid_pricing");

            migrationBuilder.DropTable(
                name: "bidder_refresh_tokens");

            migrationBuilder.DropTable(
                name: "clarification_attachments");

            migrationBuilder.DropTable(
                name: "combined_scorecards");

            migrationBuilder.DropTable(
                name: "commercial_scores");

            migrationBuilder.DropTable(
                name: "email_logs");

            migrationBuilder.DropTable(
                name: "evaluation_panels");

            migrationBuilder.DropTable(
                name: "evaluation_state");

            migrationBuilder.DropTable(
                name: "notification_preferences");

            migrationBuilder.DropTable(
                name: "refresh_tokens");

            migrationBuilder.DropTable(
                name: "system_settings");

            migrationBuilder.DropTable(
                name: "technical_scores");

            migrationBuilder.DropTable(
                name: "tender_bidders");

            migrationBuilder.DropTable(
                name: "units_of_measure");

            migrationBuilder.DropTable(
                name: "uom_master");

            migrationBuilder.DropTable(
                name: "vendor_item_rates");

            migrationBuilder.DropTable(
                name: "addenda");

            migrationBuilder.DropTable(
                name: "approval_workflows");

            migrationBuilder.DropTable(
                name: "clarifications");

            migrationBuilder.DropTable(
                name: "evaluation_criteria");

            migrationBuilder.DropTable(
                name: "boq_items");

            migrationBuilder.DropTable(
                name: "vendor_pricing_snapshots");

            migrationBuilder.DropTable(
                name: "clarification_bulletins");

            migrationBuilder.DropTable(
                name: "documents");

            migrationBuilder.DropTable(
                name: "boq_sections");

            migrationBuilder.DropTable(
                name: "bid_submissions");

            migrationBuilder.DropTable(
                name: "bidders");

            migrationBuilder.DropTable(
                name: "tenders");

            migrationBuilder.DropTable(
                name: "clients");

            migrationBuilder.DropTable(
                name: "users");
        }
    }
}
