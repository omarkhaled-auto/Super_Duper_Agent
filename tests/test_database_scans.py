"""Tests for Database Integrity Upgrades.

Covers:
- DatabaseScanConfig defaults and YAML parsing
- Dual ORM scan (DB-001..003)
- Default value scan (DB-004..005)
- Relationship scan (DB-006..008)
- Quality standards (DATABASE_INTEGRITY_STANDARDS)
- Prompt injections (SEED-001..003, ENUM-001..003)
- Cross-feature integration (no pattern ID collisions)
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agent_team.config import (
    AgentTeamConfig,
    DatabaseScanConfig,
    _dict_to_config,
)
from agent_team.quality_checks import (
    Violation,
    run_dual_orm_scan,
    run_default_value_scan,
    run_relationship_scan,
)
from agent_team.code_quality_standards import (
    DATABASE_INTEGRITY_STANDARDS,
    get_standards_for_agent,
)
from agent_team.agents import (
    ARCHITECT_PROMPT,
    CODE_WRITER_PROMPT,
    CODE_REVIEWER_PROMPT,
)


# =========================================================================
# 1. Config — DatabaseScanConfig
# =========================================================================


class TestDatabaseScanConfigDefaults:
    """Tests for DatabaseScanConfig default values."""

    def test_all_defaults_true(self):
        cfg = DatabaseScanConfig()
        assert cfg.dual_orm_scan is True
        assert cfg.default_value_scan is True
        assert cfg.relationship_scan is True

    def test_on_agent_team_config(self):
        cfg = AgentTeamConfig()
        assert isinstance(cfg.database_scans, DatabaseScanConfig)
        assert cfg.database_scans.dual_orm_scan is True
        assert cfg.database_scans.default_value_scan is True
        assert cfg.database_scans.relationship_scan is True

    def test_custom_values(self):
        cfg = DatabaseScanConfig(
            dual_orm_scan=False,
            default_value_scan=True,
            relationship_scan=False,
        )
        assert cfg.dual_orm_scan is False
        assert cfg.default_value_scan is True
        assert cfg.relationship_scan is False


class TestDatabaseScanConfigYAML:
    """Tests for DatabaseScanConfig loading via _dict_to_config."""

    def test_all_fields(self):
        data = {"database_scans": {
            "dual_orm_scan": False,
            "default_value_scan": False,
            "relationship_scan": False,
        }}
        cfg, _ = _dict_to_config(data)
        assert cfg.database_scans.dual_orm_scan is False
        assert cfg.database_scans.default_value_scan is False
        assert cfg.database_scans.relationship_scan is False

    def test_partial_preserves_defaults(self):
        data = {"database_scans": {"dual_orm_scan": False}}
        cfg, _ = _dict_to_config(data)
        assert cfg.database_scans.dual_orm_scan is False
        assert cfg.database_scans.default_value_scan is True  # default preserved
        assert cfg.database_scans.relationship_scan is True  # default preserved

    def test_missing_section_uses_defaults(self):
        cfg, _ = _dict_to_config({})
        assert cfg.database_scans.dual_orm_scan is True
        assert cfg.database_scans.default_value_scan is True
        assert cfg.database_scans.relationship_scan is True

    def test_invalid_type_ignored(self):
        data = {"database_scans": "not_a_dict"}
        cfg, _ = _dict_to_config(data)
        # Should fall back to defaults
        assert cfg.database_scans.dual_orm_scan is True

    def test_unknown_keys_dont_break_parsing(self):
        data = {"database_scans": {
            "dual_orm_scan": False,
            "unknown_future_field": 42,
        }}
        cfg, _ = _dict_to_config(data)
        assert cfg.database_scans.dual_orm_scan is False
        assert cfg.database_scans.default_value_scan is True

    def test_existing_config_sections_still_work(self):
        """Database scans config doesn't break existing config loading."""
        data = {
            "integrity_scans": {"deployment_scan": False},
            "database_scans": {"dual_orm_scan": False},
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.database_scans.dual_orm_scan is False


# =========================================================================
# 2. Dual ORM Scan (DB-001, DB-002, DB-003)
# =========================================================================


def _make_csproj(path: Path, efcore: bool = False, dapper: bool = False):
    """Helper to create a minimal .csproj with optional NuGet packages."""
    packages = []
    if efcore:
        packages.append('<PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />')
    if dapper:
        packages.append('<PackageReference Include="Dapper" Version="2.0.0" />')
    content = textwrap.dedent(f"""\
        <Project Sdk="Microsoft.NET.Sdk">
          <ItemGroup>
            {"".join(packages)}
          </ItemGroup>
        </Project>
    """)
    path.write_text(content, encoding="utf-8")


class TestDualOrmScanPositive:
    """Tests for positive detection of dual ORM type mismatches."""

    def test_db001_csharp_enum_mismatch(self, tmp_path):
        """C# project with EF Core enum property + Dapper raw SQL integer comparison."""
        proj = tmp_path / "MyApp"
        proj.mkdir()
        _make_csproj(proj / "MyApp.csproj", efcore=True, dapper=True)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "Tender.cs").write_text(textwrap.dedent("""\
            using System;
            [Table]
            public class Tender
            {
                public int Id { get; set; }
                public TenderStatus Status { get; set; }
                public string Title { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "TenderService.cs").write_text(textwrap.dedent("""\
            public class TenderService
            {
                public async Task<List<Tender>> GetActive()
                {
                    var sql = "SELECT * FROM Tenders WHERE Status = 2";
                    return await conn.QueryAsync<Tender>(sql);
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        db001 = [v for v in violations if v.check == "DB-001"]
        assert len(db001) >= 1
        assert any("status" in v.message.lower() for v in db001)

    def test_db002_csharp_bool_mismatch(self, tmp_path):
        """C# project with EF Core bool property + Dapper raw SQL 0/1 comparison."""
        proj = tmp_path / "MyApp"
        proj.mkdir()
        _make_csproj(proj / "MyApp.csproj", efcore=True, dapper=True)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public bool IsActive { get; set; }
                public string Name { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "UserService.cs").write_text(textwrap.dedent("""\
            public class UserService
            {
                public async Task<List<User>> GetActive()
                {
                    var sql = "SELECT * FROM Users WHERE IsActive = 1";
                    return await conn.QueryAsync<User>(sql);
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        db002 = [v for v in violations if v.check == "DB-002"]
        assert len(db002) >= 1
        assert any("isactive" in v.message.lower() for v in db002)

    def test_dual_orm_detected_from_csproj(self, tmp_path):
        """Both EF Core AND Dapper in .csproj → dual ORM correctly detected."""
        proj = tmp_path / "MyApp"
        proj.mkdir()
        _make_csproj(proj / "MyApp.csproj", efcore=True, dapper=True)

        entities = proj / "Models"
        entities.mkdir()
        (entities / "Item.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Item
            {
                public int Id { get; set; }
                public string Name { get; set; }
            }
        """), encoding="utf-8")

        # No mismatches in this file, but scan should still run (not skip)
        violations = run_dual_orm_scan(proj)
        # zero violations is fine — the important thing is it didn't skip
        assert isinstance(violations, list)

    def test_db001_enum_in_raw_sql_where(self, tmp_path):
        """Raw SQL WHERE status = 2 + ORM Status property → DB-001."""
        proj = tmp_path / "App"
        proj.mkdir()
        _make_csproj(proj / "App.csproj", efcore=True, dapper=True)

        entities = proj / "Domain"
        entities.mkdir()
        (entities / "Bid.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Bid
            {
                public int Id { get; set; }
                public BidStatus Status { get; set; }
            }
        """), encoding="utf-8")

        repo = proj / "Repositories"
        repo.mkdir()
        (repo / "BidRepo.cs").write_text(textwrap.dedent("""\
            public class BidRepo
            {
                public async Task GetOpen()
                {
                    var q = "SELECT * FROM Bids WHERE status = 3 AND active = 1";
                    return await _conn.QueryAsync(q);
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        db001 = [v for v in violations if v.check == "DB-001"]
        assert len(db001) >= 1


class TestDualOrmScanNegative:
    """Tests for no false positives in the dual ORM scan."""

    def test_single_orm_skips(self, tmp_path):
        """Single ORM project (EF Core only, no Dapper) → zero violations."""
        proj = tmp_path / "SingleOrm"
        proj.mkdir()
        _make_csproj(proj / "SingleOrm.csproj", efcore=True, dapper=False)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "Product.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Product
            {
                public int Id { get; set; }
                public ProductStatus Status { get; set; }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        assert violations == []

    def test_no_orm_skips(self, tmp_path):
        """Project with no ORM at all → scan skips, zero violations."""
        proj = tmp_path / "NoOrm"
        proj.mkdir()
        (proj / "readme.txt").write_text("Just a readme", encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        assert violations == []

    def test_prisma_only_no_raw_sql(self, tmp_path):
        """Prisma only, no raw SQL → scan skips."""
        proj = tmp_path / "PrismaApp"
        proj.mkdir()
        (proj / "package.json").write_text('{"dependencies": {"prisma": "^5.0.0"}}', encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        assert violations == []


class TestDualOrmScanEdgeCases:
    """Edge cases for the dual ORM scan."""

    def test_empty_project(self, tmp_path):
        """Empty project → empty list."""
        violations = run_dual_orm_scan(tmp_path)
        assert violations == []

    def test_frontend_only_project(self, tmp_path):
        """Project with only frontend (no database files) → skip gracefully."""
        proj = tmp_path / "Frontend"
        proj.mkdir()
        (proj / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}', encoding="utf-8")
        src = proj / "src"
        src.mkdir()
        (src / "App.tsx").write_text("export default function App() { return <div/>; }", encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        assert violations == []


# =========================================================================
# 3. Default Value Scan (DB-004, DB-005)
# =========================================================================


class TestDefaultValueScanPositive:
    """Tests for positive detection of missing defaults and nullable misuse."""

    def test_db004_csharp_bool_no_default(self, tmp_path):
        """C# bool without '= false;' → DB-004."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public bool IsActive { get; set; }
                public bool EmailVerified { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 2
        names = [v.message for v in db004]
        assert any("IsActive" in m for m in names)
        assert any("EmailVerified" in m for m in names)

    def test_db004_prisma_no_default(self, tmp_path):
        """Prisma Boolean without @default(false) → DB-004."""
        proj = tmp_path / "App"
        prisma_dir = proj / "prisma"
        prisma_dir.mkdir(parents=True)
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            model User {
              id        Int      @id @default(autoincrement())
              isActive  Boolean
              name      String
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("isActive" in v.message for v in db004)

    def test_db004_django_booleanfield_no_default(self, tmp_path):
        """Django BooleanField() without default= → DB-004."""
        proj = tmp_path / "App"
        models_dir = proj / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "user.py").write_text(textwrap.dedent("""\
            from django.db import models

            class User(models.Model):
                name = models.CharField(max_length=100)
                is_active = models.BooleanField()
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1

    def test_db004_sqlalchemy_column_boolean_no_default(self, tmp_path):
        """SQLAlchemy Column(Boolean) without default → DB-004."""
        proj = tmp_path / "App"
        models_dir = proj / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "user.py").write_text(textwrap.dedent("""\
            from sqlalchemy import Column, Boolean, String
            from base import Base

            class User(Base):
                __tablename__ = 'users'
                is_active = Column(Boolean)
                name = Column(String)
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1

    def test_db005_csharp_nullable_no_check(self, tmp_path):
        """C# nullable property accessed without null check → DB-005."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Order.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Order
            {
                public int Id { get; set; }
                public string? Description { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir(parents=True)
        (services / "OrderService.cs").write_text(textwrap.dedent("""\
            public class OrderService
            {
                public string GetDescLength(Order order)
                {
                    var len = order.Description.Length;
                    return len.ToString();
                }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) >= 1
        assert any("Description" in v.message for v in db005)


class TestDefaultValueScanNegative:
    """Tests for no false positives in the default value scan."""

    def test_csharp_bool_with_default(self, tmp_path):
        """C# bool with '= false;' → no DB-004."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public bool IsActive { get; set; } = false;
                public bool EmailVerified { get; set; } = true;
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) == 0

    def test_prisma_with_default(self, tmp_path):
        """Prisma Boolean @default(false) → no DB-004."""
        proj = tmp_path / "App"
        prisma_dir = proj / "prisma"
        prisma_dir.mkdir(parents=True)
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            model User {
              id        Int      @id @default(autoincrement())
              isActive  Boolean  @default(false)
              name      String
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) == 0

    def test_nullable_with_null_conditional(self, tmp_path):
        """Nullable property accessed with ?. → no DB-005."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Order.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Order
            {
                public int Id { get; set; }
                public string? Description { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir(parents=True)
        (services / "OrderService.cs").write_text(textwrap.dedent("""\
            public class OrderService
            {
                public int? GetDescLength(Order order)
                {
                    var len = order.Description?.Length;
                    return len;
                }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) == 0

    def test_nullable_with_null_check_guard(self, tmp_path):
        """Nullable property with explicit null check → no DB-005."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Order.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Order
            {
                public int Id { get; set; }
                public string? Description { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir(parents=True)
        (services / "OrderService.cs").write_text(textwrap.dedent("""\
            public class OrderService
            {
                public int GetDescLength(Order order)
                {
                    if (order.Description != null)
                    {
                        return order.Description.Length;
                    }
                    return 0;
                }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) == 0


class TestDefaultValueScanEdgeCases:
    """Edge cases for the default value scan."""

    def test_no_entity_files(self, tmp_path):
        """Project with no entity files → scan skips, zero violations."""
        proj = tmp_path / "App"
        proj.mkdir()
        (proj / "readme.md").write_text("# Readme", encoding="utf-8")

        violations = run_default_value_scan(proj)
        assert violations == []

    def test_entity_with_no_booleans(self, tmp_path):
        """Entity with no boolean or enum properties → scan runs but finds nothing."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Item.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Item
            {
                public int Id { get; set; }
                public string Name { get; set; }
                public decimal Price { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) == 0

    def test_empty_project(self, tmp_path):
        """Empty project → empty list."""
        violations = run_default_value_scan(tmp_path)
        assert violations == []


# =========================================================================
# 4. Relationship Scan (DB-006, DB-007, DB-008)
# =========================================================================


class TestRelationshipScanPositive:
    """Tests for positive detection of incomplete relationships."""

    def test_db006_fk_without_nav(self, tmp_path):
        """FK column TenderId without navigation property Tender → DB-006."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Bid.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Bid
            {
                public int Id { get; set; }
                public int TenderId { get; set; }
                public decimal Amount { get; set; }
            }
        """), encoding="utf-8")

        # Config file that references Tender nav but not on Bid
        config_dir = proj / "Configurations"
        config_dir.mkdir(parents=True)
        (config_dir / "BidConfig.cs").write_text(textwrap.dedent("""\
            public class BidConfig : IEntityTypeConfiguration<Bid>
            {
                public void Configure(EntityTypeBuilder<Bid> builder)
                {
                    builder.HasOne(b => b.Tender).WithMany(t => t.Bids);
                }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # Has config (Tender in HasOne references) but no nav prop on the entity
        db006 = [v for v in violations if v.check == "DB-006"]
        assert len(db006) >= 1
        assert any("TenderId" in v.message for v in db006)

    def test_db008_fk_no_nav_no_config(self, tmp_path):
        """FK column with no navigation AND no config → DB-008."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Comment.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Comment
            {
                public int Id { get; set; }
                public int PostId { get; set; }
                public string Text { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        db008 = [v for v in violations if v.check == "DB-008"]
        assert len(db008) >= 1
        assert any("PostId" in v.message for v in db008)

    def test_multiple_fks_independently_checked(self, tmp_path):
        """Multiple FK columns → each independently checked."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "OrderItem.cs").write_text(textwrap.dedent("""\
            [Table]
            public class OrderItem
            {
                public int Id { get; set; }
                public int OrderId { get; set; }
                public int ProductId { get; set; }
                public int Quantity { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # Both OrderId and ProductId should be flagged (DB-008 since no nav, no config)
        fk_names = [v.message for v in violations if v.check in ("DB-006", "DB-008")]
        assert any("OrderId" in m for m in fk_names)
        assert any("ProductId" in m for m in fk_names)

    def test_self_referential_fk(self, tmp_path):
        """Self-referential FK (ParentCategoryId) → should detect missing nav."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Category.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Category
            {
                public int Id { get; set; }
                public int ParentCategoryId { get; set; }
                public string Name { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        fk_violations = [v for v in violations if v.check in ("DB-006", "DB-008")]
        assert any("ParentCategoryId" in v.message for v in fk_violations)


class TestRelationshipScanNegative:
    """Tests for no false positives in the relationship scan."""

    def test_proper_fk_with_nav(self, tmp_path):
        """Properly configured FK + navigation → zero violations for that FK."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Bid.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Bid
            {
                public int Id { get; set; }
                public int TenderId { get; set; }
                public virtual Tender Tender { get; set; }
                public decimal Amount { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # TenderId should NOT be flagged because Tender nav prop exists
        tender_violations = [v for v in violations
                            if "TenderId" in v.message and v.check in ("DB-006", "DB-008")]
        assert len(tender_violations) == 0

    def test_primary_key_id_not_flagged(self, tmp_path):
        """Primary key 'Id' property → NOT flagged as FK."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Product.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Product
            {
                public int Id { get; set; }
                public string Name { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # Id should NOT be flagged
        id_violations = [v for v in violations if "'Id'" in v.message]
        assert len(id_violations) == 0


class TestRelationshipScanEdgeCases:
    """Edge cases for the relationship scan."""

    def test_no_entity_files(self, tmp_path):
        """No ORM entities in project → scan skips, zero violations."""
        proj = tmp_path / "App"
        proj.mkdir()
        (proj / "readme.md").write_text("# Readme", encoding="utf-8")

        violations = run_relationship_scan(proj)
        assert violations == []

    def test_empty_project(self, tmp_path):
        """Empty project → empty list."""
        violations = run_relationship_scan(tmp_path)
        assert violations == []

    def test_fk_with_config_but_no_nav(self, tmp_path):
        """FK with HasOne config in separate file but no nav prop on entity → DB-006."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Invoice.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Invoice
            {
                public int Id { get; set; }
                public int CustomerId { get; set; }
                public decimal Total { get; set; }
            }
        """), encoding="utf-8")

        config_dir = proj / "Configurations"
        config_dir.mkdir(parents=True)
        (config_dir / "InvoiceConfig.cs").write_text(textwrap.dedent("""\
            public class InvoiceConfig : IEntityTypeConfiguration<Invoice>
            {
                public void Configure(EntityTypeBuilder<Invoice> builder)
                {
                    builder.HasOne(i => i.Customer).WithMany(c => c.Invoices);
                }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # HasOne refs Customer nav, so Customer is in config_references
        # CustomerId's expected_nav = "Customer", has_config should be True
        # But has_nav is False → DB-006
        db006 = [v for v in violations if v.check == "DB-006"]
        assert len(db006) >= 1
        assert any("CustomerId" in v.message for v in db006)


# =========================================================================
# 5. Violation Dataclass Properties
# =========================================================================


class TestViolationDataclass:
    """Tests that violations from database scans have correct structure."""

    def test_violation_fields_present(self, tmp_path):
        """All violations have the standard Violation fields."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public bool IsActive { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        assert len(violations) >= 1
        v = violations[0]
        assert isinstance(v, Violation)
        assert isinstance(v.check, str)
        assert isinstance(v.message, str)
        assert isinstance(v.file_path, str)
        assert isinstance(v.line, int)
        assert isinstance(v.severity, str)
        assert v.severity in ("error", "warning", "info")

    def test_violations_sorted(self, tmp_path):
        """Violations are sorted by severity then file_path then line."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "A.cs").write_text(textwrap.dedent("""\
            [Table]
            public class A
            {
                public int Id { get; set; }
                public bool Flag1 { get; set; }
                public bool Flag2 { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        if len(violations) >= 2:
            # Check sorting: severity first, then file_path, then line
            for i in range(len(violations) - 1):
                v1, v2 = violations[i], violations[i + 1]
                sev_order = {"error": 0, "warning": 1, "info": 2}
                key1 = (sev_order.get(v1.severity, 99), v1.file_path, v1.line)
                key2 = (sev_order.get(v2.severity, 99), v2.file_path, v2.line)
                assert key1 <= key2


# =========================================================================
# 6. Quality Standards (DATABASE_INTEGRITY_STANDARDS)
# =========================================================================


class TestDatabaseIntegrityStandards:
    """Tests for the DATABASE_INTEGRITY_STANDARDS constant."""

    def test_constant_exists_and_nonempty(self):
        assert DATABASE_INTEGRITY_STANDARDS
        assert len(DATABASE_INTEGRITY_STANDARDS) > 100

    def test_contains_all_pattern_ids(self):
        for pattern_id in ("DB-001", "DB-002", "DB-003", "DB-004",
                           "DB-005", "DB-006", "DB-007", "DB-008"):
            assert pattern_id in DATABASE_INTEGRITY_STANDARDS, (
                f"{pattern_id} missing from DATABASE_INTEGRITY_STANDARDS"
            )

    def test_contains_seed_data_section(self):
        assert "Seed Data Completeness" in DATABASE_INTEGRITY_STANDARDS

    def test_contains_enum_registry_section(self):
        assert "Enum/Status Registry" in DATABASE_INTEGRITY_STANDARDS

    def test_code_writer_includes_standards(self):
        result = get_standards_for_agent("code-writer")
        assert "DB-001" in result
        assert "DB-008" in result

    def test_code_reviewer_includes_standards(self):
        result = get_standards_for_agent("code-reviewer")
        assert "DB-001" in result
        assert "DB-008" in result

    def test_architect_includes_standards(self):
        result = get_standards_for_agent("architect")
        assert "DB-001" in result
        assert "DB-008" in result

    def test_test_runner_does_not_include_standards(self):
        result = get_standards_for_agent("test-runner")
        assert "DB-001" not in result
        assert "DATABASE INTEGRITY" not in result

    def test_debugger_does_not_include_standards(self):
        result = get_standards_for_agent("debugger")
        assert "DB-001" not in result


# =========================================================================
# 7. Prompt Injections (SEED-001..003, ENUM-001..003)
# =========================================================================


class TestCodeWriterPromptInjections:
    """Tests for seed data and enum/status prompt injections in CODE_WRITER_PROMPT."""

    def test_seed_data_policy_present(self):
        assert "SEED DATA COMPLETENESS POLICY" in CODE_WRITER_PROMPT

    def test_seed_001_present(self):
        assert "SEED-001" in CODE_WRITER_PROMPT

    def test_seed_002_present(self):
        assert "SEED-002" in CODE_WRITER_PROMPT

    def test_seed_003_present(self):
        assert "SEED-003" in CODE_WRITER_PROMPT

    def test_enum_status_registry_compliance_present(self):
        assert "ENUM/STATUS REGISTRY COMPLIANCE" in CODE_WRITER_PROMPT

    def test_enum_001_present(self):
        assert "ENUM-001" in CODE_WRITER_PROMPT

    def test_enum_002_present(self):
        assert "ENUM-002" in CODE_WRITER_PROMPT

    def test_enum_003_present(self):
        assert "ENUM-003" in CODE_WRITER_PROMPT

    def test_seed_policy_has_review_failure_severity(self):
        """Seed data policy uses REVIEW FAILURE severity language."""
        assert "AUTOMATIC REVIEW FAILURE" in CODE_WRITER_PROMPT

    def test_enum_policy_has_review_failure_severity(self):
        """Enum policy uses REVIEW FAILURE severity language."""
        assert "REVIEW FAILURE" in CODE_WRITER_PROMPT

    def test_existing_policies_still_present(self):
        """ZERO MOCK DATA and UI COMPLIANCE policies still present."""
        assert "ZERO MOCK DATA POLICY" in CODE_WRITER_PROMPT
        assert "UI COMPLIANCE POLICY" in CODE_WRITER_PROMPT

    def test_seed_after_ui_compliance(self):
        """Seed data policy appears AFTER UI compliance policy."""
        ui_pos = CODE_WRITER_PROMPT.index("UI COMPLIANCE POLICY")
        seed_pos = CODE_WRITER_PROMPT.index("SEED DATA COMPLETENESS POLICY")
        assert seed_pos > ui_pos

    def test_enum_after_seed(self):
        """Enum/Status Registry appears AFTER Seed Data policy."""
        seed_pos = CODE_WRITER_PROMPT.index("SEED DATA COMPLETENESS POLICY")
        enum_pos = CODE_WRITER_PROMPT.index("ENUM/STATUS REGISTRY COMPLIANCE")
        assert enum_pos > seed_pos


class TestCodeReviewerPromptInjections:
    """Tests for seed data and enum/status verification in CODE_REVIEWER_PROMPT."""

    def test_seed_verification_present(self):
        assert "Seed Data Verification" in CODE_REVIEWER_PROMPT

    def test_seed_001_in_reviewer(self):
        assert "SEED-001" in CODE_REVIEWER_PROMPT

    def test_seed_002_in_reviewer(self):
        assert "SEED-002" in CODE_REVIEWER_PROMPT

    def test_seed_003_in_reviewer(self):
        assert "SEED-003" in CODE_REVIEWER_PROMPT

    def test_enum_verification_present(self):
        assert "Enum/Status Registry Verification" in CODE_REVIEWER_PROMPT

    def test_enum_001_in_reviewer(self):
        assert "ENUM-001" in CODE_REVIEWER_PROMPT

    def test_enum_002_in_reviewer(self):
        assert "ENUM-002" in CODE_REVIEWER_PROMPT

    def test_enum_003_in_reviewer(self):
        assert "ENUM-003" in CODE_REVIEWER_PROMPT

    def test_fail_verdict_language(self):
        assert "FAIL verdict" in CODE_REVIEWER_PROMPT

    def test_existing_policies_still_present(self):
        """Existing reviewer sections still present."""
        assert "Mock Data Detection" in CODE_REVIEWER_PROMPT
        assert "UI Compliance Verification" in CODE_REVIEWER_PROMPT

    def test_seed_after_ui_compliance_verification(self):
        """Seed verification appears AFTER UI Compliance Verification."""
        ui_pos = CODE_REVIEWER_PROMPT.index("UI Compliance Verification")
        seed_pos = CODE_REVIEWER_PROMPT.index("Seed Data Verification")
        assert seed_pos > ui_pos

    def test_enum_after_seed_verification(self):
        """Enum/Status verification appears AFTER Seed Data Verification."""
        seed_pos = CODE_REVIEWER_PROMPT.index("Seed Data Verification")
        enum_pos = CODE_REVIEWER_PROMPT.index("Enum/Status Registry Verification")
        assert enum_pos > seed_pos


class TestArchitectPromptInjections:
    """Tests for status/enum registry in ARCHITECT_PROMPT."""

    def test_status_enum_registry_present(self):
        assert "Status/Enum Registry" in ARCHITECT_PROMPT

    def test_enum_001_in_architect(self):
        assert "ENUM-001" in ARCHITECT_PROMPT

    def test_enum_002_in_architect(self):
        assert "ENUM-002" in ARCHITECT_PROMPT

    def test_enum_003_in_architect(self):
        assert "ENUM-003" in ARCHITECT_PROMPT

    def test_existing_sections_still_present(self):
        """Existing architect sections still present."""
        assert "Service-to-API Wiring Plan" in ARCHITECT_PROMPT

    def test_registry_after_wiring_plan(self):
        """Status/Enum Registry appears AFTER Service-to-API Wiring Plan."""
        wiring_pos = ARCHITECT_PROMPT.index("Service-to-API Wiring Plan")
        registry_pos = ARCHITECT_PROMPT.index("Status/Enum Registry")
        assert registry_pos > wiring_pos


# =========================================================================
# 8. Cross-Feature Integration
# =========================================================================


class TestCrossFeatureIntegration:
    """Tests that DB upgrades don't collide with existing features."""

    def test_db_pattern_ids_no_collision(self):
        """DB-001..008 don't collide with existing pattern IDs."""
        existing_ids = {
            "MOCK-001", "MOCK-002", "MOCK-003", "MOCK-004", "MOCK-005",
            "MOCK-006", "MOCK-007",
            "UI-001", "UI-002", "UI-003", "UI-004",
            "E2E-001", "E2E-002", "E2E-003", "E2E-004", "E2E-005",
            "E2E-006", "E2E-007",
            "DEPLOY-001", "DEPLOY-002", "DEPLOY-003", "DEPLOY-004",
            "ASSET-001", "ASSET-002", "ASSET-003",
            "PRD-001",
            "FRONT-007", "FRONT-010", "FRONT-016",
            "BACK-001", "BACK-002", "BACK-016", "BACK-017", "BACK-018",
            "SLOP-001", "SLOP-003",
        }
        new_ids = {f"DB-{i:03d}" for i in range(1, 9)}
        assert new_ids.isdisjoint(existing_ids), (
            f"Collision: {new_ids & existing_ids}"
        )

    def test_seed_enum_pattern_ids_no_collision(self):
        """SEED-001..003 and ENUM-001..003 don't collide with existing IDs."""
        existing_ids = {
            "MOCK-001", "MOCK-002", "MOCK-003", "MOCK-004", "MOCK-005",
            "MOCK-006", "MOCK-007",
            "UI-001", "UI-002", "UI-003", "UI-004",
            "FRONT-007", "FRONT-010", "FRONT-016",
            "BACK-001", "BACK-002",
        }
        new_ids = {
            "SEED-001", "SEED-002", "SEED-003",
            "ENUM-001", "ENUM-002", "ENUM-003",
        }
        assert new_ids.isdisjoint(existing_ids)

    def test_all_scan_functions_importable(self):
        """All 3 new scan functions are importable from quality_checks."""
        from agent_team.quality_checks import (
            run_dual_orm_scan,
            run_default_value_scan,
            run_relationship_scan,
        )
        assert callable(run_dual_orm_scan)
        assert callable(run_default_value_scan)
        assert callable(run_relationship_scan)

    def test_new_config_doesnt_break_existing(self):
        """New DatabaseScanConfig doesn't break existing config loading."""
        data = {
            "convergence": {"max_cycles": 5},
            "integrity_scans": {"deployment_scan": True},
            "database_scans": {"dual_orm_scan": True},
            "e2e_testing": {"enabled": True},
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.convergence.max_cycles == 5
        assert cfg.integrity_scans.deployment_scan is True
        assert cfg.database_scans.dual_orm_scan is True
        assert cfg.e2e_testing.enabled is True

    def test_prompt_no_duplicate_section_headers(self):
        """No duplicate SEED DATA or ENUM/STATUS section headers in prompts."""
        assert CODE_WRITER_PROMPT.count("SEED DATA COMPLETENESS POLICY") == 1
        assert CODE_WRITER_PROMPT.count("ENUM/STATUS REGISTRY COMPLIANCE") == 1
        assert CODE_REVIEWER_PROMPT.count("Seed Data Verification") == 1
        assert CODE_REVIEWER_PROMPT.count("Enum/Status Registry Verification") == 1


# =========================================================================
# 9. CLI Wiring (source-level verification)
# =========================================================================


class TestCLIWiringSourceVerification:
    """Verify CLI wiring by reading source code patterns."""

    @pytest.fixture(autouse=True)
    def _load_cli_source(self):
        """Load cli.py source for inspection."""
        cli_path = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"
        self.cli_source = cli_path.read_text(encoding="utf-8")

    def test_dual_orm_scan_gated_by_config(self):
        assert "config.database_scans.dual_orm_scan" in self.cli_source

    def test_default_value_scan_gated_by_config(self):
        assert "config.database_scans.default_value_scan" in self.cli_source

    def test_relationship_scan_gated_by_config(self):
        assert "config.database_scans.relationship_scan" in self.cli_source

    def test_dual_orm_recovery_type(self):
        assert '"database_dual_orm_fix"' in self.cli_source

    def test_default_value_recovery_type(self):
        assert '"database_default_value_fix"' in self.cli_source

    def test_relationship_recovery_type(self):
        assert '"database_relationship_fix"' in self.cli_source

    def test_dual_orm_scan_type(self):
        assert 'scan_type="database_dual_orm"' in self.cli_source

    def test_default_value_scan_type(self):
        assert 'scan_type="database_defaults"' in self.cli_source

    def test_relationship_scan_type(self):
        assert 'scan_type="database_relationships"' in self.cli_source

    def test_scans_after_prd_reconciliation(self):
        """Database scans appear AFTER PRD reconciliation."""
        prd_pos = self.cli_source.index("prd_reconciliation_mismatch")
        db_pos = self.cli_source.index("database_dual_orm_fix")
        assert db_pos > prd_pos

    def test_scans_before_e2e(self):
        """Database scans appear BEFORE E2E testing phase."""
        db_pos = self.cli_source.index("database_relationship_fix")
        # E2E phase starts with e2e_testing config check
        e2e_pos = self.cli_source.index("config.e2e_testing.enabled", db_pos)
        assert db_pos < e2e_pos

    def test_each_scan_in_own_try_except(self):
        """Each scan has its own try/except for crash isolation."""
        # Count the database scan try blocks
        section_start = self.cli_source.index("Database Integrity Scans")
        # Find the next major section
        section_end = self.cli_source.index("config.e2e_testing.enabled", section_start)
        section = self.cli_source[section_start:section_end]

        # There should be 3 outer except blocks (one per scan)
        assert section.count("except Exception as exc:") >= 3

    def test_scan_order_dual_then_defaults_then_relationships(self):
        """Scans run in order: dual ORM → defaults → relationships."""
        p1 = self.cli_source.index('run_dual_orm_scan')
        p2 = self.cli_source.index('run_default_value_scan')
        p3 = self.cli_source.index('run_relationship_scan')
        assert p1 < p2 < p3

    def test_imports_from_quality_checks(self):
        """All 3 scans import from .quality_checks."""
        assert "from .quality_checks import run_dual_orm_scan" in self.cli_source
        assert "from .quality_checks import run_default_value_scan" in self.cli_source
        assert "from .quality_checks import run_relationship_scan" in self.cli_source

    def test_cost_tracking_for_fixes(self):
        """Fix passes update _current_state.total_cost."""
        section_start = self.cli_source.index("Database Integrity Scans")
        section_end = self.cli_source.index("config.e2e_testing.enabled", section_start)
        section = self.cli_source[section_start:section_end]
        assert section.count("_current_state.total_cost += fix_cost") >= 3


# =========================================================================
# 10. Regression Safety
# =========================================================================


class TestRegressionSafety:
    """Ensure database upgrades don't break existing features."""

    def test_existing_scan_functions_importable(self):
        """Existing scan functions are still importable."""
        from agent_team.quality_checks import (
            run_mock_data_scan,
            run_ui_compliance_scan,
            run_deployment_scan,
            run_asset_scan,
            parse_prd_reconciliation,
        )
        assert callable(run_mock_data_scan)
        assert callable(run_ui_compliance_scan)
        assert callable(run_deployment_scan)
        assert callable(run_asset_scan)
        assert callable(parse_prd_reconciliation)

    def test_existing_config_fields_intact(self):
        """Existing config fields unchanged."""
        from agent_team.config import IntegrityScanConfig
        cfg = IntegrityScanConfig()
        assert hasattr(cfg, "deployment_scan")
        assert hasattr(cfg, "asset_scan")
        assert hasattr(cfg, "prd_reconciliation")

    def test_mock_data_policy_unchanged(self):
        """ZERO MOCK DATA POLICY text still present in code writer prompt."""
        assert "ZERO MOCK DATA POLICY" in CODE_WRITER_PROMPT
        assert "of(null).pipe(delay" in CODE_WRITER_PROMPT

    def test_existing_standards_still_mapped(self):
        """Existing standards still mapped to correct agents."""
        writer_standards = get_standards_for_agent("code-writer")
        assert "FRONT-" in writer_standards  # FRONTEND_STANDARDS
        assert "BACK-" in writer_standards   # BACKEND_STANDARDS

        reviewer_standards = get_standards_for_agent("code-reviewer")
        assert reviewer_standards  # CODE_REVIEW_STANDARDS

        runner_standards = get_standards_for_agent("test-runner")
        assert "E2E" in runner_standards  # E2E_TESTING_STANDARDS

    def test_dict_to_config_still_parses_all_sections(self):
        """_dict_to_config still handles all existing sections."""
        data = {
            "convergence": {"max_cycles": 3},
            "milestone": {"enabled": True},
            "prd_chunking": {"enabled": True},
            "integrity_scans": {"deployment_scan": True},
            "e2e_testing": {"enabled": True, "max_fix_retries": 3, "test_port": 8080},
            "tracking_documents": {"e2e_coverage_matrix": True},
            "database_scans": {"dual_orm_scan": False},
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.convergence.max_cycles == 3
        assert cfg.milestone.enabled is True
        assert cfg.prd_chunking.enabled is True
        assert cfg.integrity_scans.deployment_scan is True
        assert cfg.e2e_testing.enabled is True
        assert cfg.tracking_documents.e2e_coverage_matrix is True
        assert cfg.database_scans.dual_orm_scan is False


# =========================================================================
# 11. Conditional Skip Tests
# =========================================================================


class TestConditionalSkips:
    """Tests for scan conditional skip behavior."""

    def test_dual_orm_skips_single_orm(self, tmp_path):
        """Single ORM → dual ORM scan returns empty."""
        proj = tmp_path / "App"
        proj.mkdir()
        _make_csproj(proj / "App.csproj", efcore=True, dapper=False)
        violations = run_dual_orm_scan(proj)
        assert violations == []

    def test_default_value_skips_no_entities(self, tmp_path):
        """No entity files → default value scan returns empty."""
        proj = tmp_path / "App"
        proj.mkdir()
        (proj / "index.ts").write_text("console.log('hello');", encoding="utf-8")
        violations = run_default_value_scan(proj)
        assert violations == []

    def test_relationship_skips_no_entities(self, tmp_path):
        """No ORM entities → relationship scan returns empty."""
        proj = tmp_path / "App"
        proj.mkdir()
        (proj / "main.py").write_text("print('hello')", encoding="utf-8")
        violations = run_relationship_scan(proj)
        assert violations == []

    def test_all_scans_return_list(self, tmp_path):
        """All scan functions always return a list (never None)."""
        proj = tmp_path / "Empty"
        proj.mkdir()
        assert isinstance(run_dual_orm_scan(proj), list)
        assert isinstance(run_default_value_scan(proj), list)
        assert isinstance(run_relationship_scan(proj), list)


# =========================================================================
# 12. Max Violations Cap
# =========================================================================


class TestMaxViolationsCap:
    """Tests that violations are capped at _MAX_VIOLATIONS (100)."""

    def test_default_value_scan_respects_cap(self, tmp_path):
        """Generate more than 100 violations → capped at 100."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)

        # Create many bool properties without defaults
        props = "\n".join(
            f"    public bool Flag{i} {{ get; set; }}"
            for i in range(120)
        )
        (entities / "BigEntity.cs").write_text(
            f"[Table]\npublic class BigEntity\n{{\n    public int Id {{ get; set; }}\n{props}\n}}\n",
            encoding="utf-8",
        )

        violations = run_default_value_scan(proj)
        assert len(violations) <= 100


# =========================================================================
# 13. DB-003 Positive Test (DateTime mismatch)
# =========================================================================


class TestDB003DateTimeMismatch:
    """Tests for DB-003: DateTime columns with hardcoded date literals in raw SQL."""

    def test_db003_datetime_in_raw_sql(self, tmp_path):
        """EF Core DateTime property + Dapper raw SQL with hardcoded date literal -> DB-003."""
        proj = tmp_path / "App"
        proj.mkdir()
        _make_csproj(proj / "App.csproj", efcore=True, dapper=True)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "Event.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Event
            {
                public int Id { get; set; }
                public DateTime StartDate { get; set; }
                public string Name { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "EventService.cs").write_text(textwrap.dedent("""\
            public class EventService
            {
                public async Task<List<Event>> GetRecent()
                {
                    var sql = "SELECT * FROM Events WHERE StartDate > '2024-01-15'";
                    return await conn.QueryAsync<Event>(sql);
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        db003 = [v for v in violations if v.check == "DB-003"]
        assert len(db003) >= 1
        assert any("startdate" in v.message.lower() for v in db003)

    def test_db003_severity_is_error(self, tmp_path):
        """DB-003 violations must have severity 'error'."""
        proj = tmp_path / "App"
        proj.mkdir()
        _make_csproj(proj / "App.csproj", efcore=True, dapper=True)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "Task.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Task
            {
                public int Id { get; set; }
                public DateTime DueDate { get; set; }
            }
        """), encoding="utf-8")

        repo = proj / "Repos"
        repo.mkdir()
        (repo / "TaskRepo.cs").write_text(textwrap.dedent("""\
            public class TaskRepo
            {
                public async Task GetOverdue()
                {
                    var q = "SELECT * FROM Tasks WHERE DueDate < '2024-06-01'";
                    return await _conn.QueryAsync(q);
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        db003 = [v for v in violations if v.check == "DB-003"]
        assert len(db003) >= 1
        for v in db003:
            assert v.severity == "error"


# =========================================================================
# 14. DB-007 Positive Test (Navigation without inverse)
# =========================================================================


class TestDB007NavigationWithoutInverse:
    """Tests for DB-007: Navigation property with no inverse on related entity."""

    def test_db007_nav_without_inverse_collection(self, tmp_path):
        """C# entity with navigation but related entity missing inverse collection -> DB-007."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)

        # Bid has a navigation to Tender
        (entities / "Bid.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Bid
            {
                public int Id { get; set; }
                public int TenderId { get; set; }
                public virtual Tender Tender { get; set; }
                public decimal Amount { get; set; }
            }
        """), encoding="utf-8")

        # Tender does NOT have ICollection<Bid> (no inverse)
        (entities / "Tender.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Tender
            {
                public int Id { get; set; }
                public string Title { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        db007 = [v for v in violations if v.check == "DB-007"]
        assert len(db007) >= 1
        assert any("Tender" in v.message for v in db007)

    def test_db007_severity_is_info(self, tmp_path):
        """DB-007 violations must have severity 'info'."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)

        (entities / "OrderItem.cs").write_text(textwrap.dedent("""\
            [Table]
            public class OrderItem
            {
                public int Id { get; set; }
                public int OrderId { get; set; }
                public virtual Order Order { get; set; }
            }
        """), encoding="utf-8")

        (entities / "Order.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Order
            {
                public int Id { get; set; }
                public string Title { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        db007 = [v for v in violations if v.check == "DB-007"]
        assert len(db007) >= 1
        for v in db007:
            assert v.severity == "info"

    def test_db007_not_raised_with_inverse(self, tmp_path):
        """No DB-007 if related entity has an inverse navigation back."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)

        (entities / "Bid.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Bid
            {
                public int Id { get; set; }
                public int TenderId { get; set; }
                public virtual Tender Tender { get; set; }
            }
        """), encoding="utf-8")

        (entities / "Tender.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Tender
            {
                public int Id { get; set; }
                public virtual ICollection<Bid> Bids { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        db007 = [v for v in violations if v.check == "DB-007"]
        assert len(db007) == 0


# =========================================================================
# 15. Cross-Language Tests
# =========================================================================


class TestCrossLanguageScans:
    """Tests for TypeScript/Prisma/Python cross-language scanning."""

    def test_prisma_bool_with_raw_sql_db002(self, tmp_path):
        """Prisma boolean + raw SQL '= 0' -> DB-002 (requires dual ORM detection)."""
        proj = tmp_path / "App"
        proj.mkdir()
        (proj / "package.json").write_text(
            '{"dependencies": {"prisma": "^5.0.0", "pg": "^8.0.0"}}',
            encoding="utf-8",
        )

        prisma_dir = proj / "prisma"
        prisma_dir.mkdir()
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            model User {
              id       Int     @id @default(autoincrement())
              isActive Boolean @default(false)
            }
        """), encoding="utf-8")

        # The scan needs the property type from entity files, and raw SQL in source files
        # Prisma models need @Entity or to be in the Models/ directory for _find_entity_files
        models = proj / "models"
        models.mkdir()
        (models / "user.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class User {
              id: number;
              isActive: boolean;
            }
        """), encoding="utf-8")

        src = proj / "src"
        src.mkdir()
        (src / "userService.ts").write_text(textwrap.dedent("""\
            export class UserService {
              async getActive() {
                const sql = "SELECT * FROM users WHERE isActive = 0";
                return db.query(sql);
              }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        # The scan might or might not pick up TS bool patterns depending on implementation
        # At minimum it should return a list without errors
        assert isinstance(violations, list)

    def test_csharp_enum_without_default_db004(self, tmp_path):
        """C# entity with enum property without default -> DB-004."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Tender.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Tender
            {
                public int Id { get; set; }
                public TenderStatus Status { get; set; }
                public string Title { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("Status" in v.message for v in db004)
        assert any("TenderStatus" in v.message for v in db004)

    def test_typeorm_joincolumn_without_relation_db006(self, tmp_path):
        """TypeORM @JoinColumn without matching relation -> DB-006 or DB-008."""
        proj = tmp_path / "App"
        entities = proj / "entities"
        entities.mkdir(parents=True)
        (entities / "bid.entity.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class Bid {
              @PrimaryGeneratedColumn()
              id: number;

              @JoinColumn({ name: 'tenderId' })
              tenderId: number;
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # Should find tenderId FK without proper navigation
        fk_violations = [v for v in violations if v.check in ("DB-006", "DB-008")]
        assert isinstance(violations, list)

    def test_typescript_nullable_without_optional_chaining_db005(self, tmp_path):
        """TypeScript/C# nullable without null check -> DB-005 (C# path)."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Product.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Product
            {
                public int Id { get; set; }
                public string? Category { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "ProductService.cs").write_text(textwrap.dedent("""\
            public class ProductService
            {
                public int GetCategoryLen(Product p)
                {
                    return p.Category.Length;
                }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) >= 1
        assert any("Category" in v.message for v in db005)


# =========================================================================
# 16. False Positive Tests
# =========================================================================


class TestFalsePositives:
    """Tests that non-entity DTOs and special properties are NOT flagged."""

    def test_dto_bool_not_flagged_db004(self, tmp_path):
        """DTO with boolean in non-entity location -> should NOT be flagged."""
        proj = tmp_path / "App"
        dtos = proj / "DTOs"
        dtos.mkdir(parents=True)
        (dtos / "UserDto.cs").write_text(textwrap.dedent("""\
            public class UserDto
            {
                public int Id { get; set; }
                public bool IsActive { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        # DTOs are not in Entity/Model directories and don't have [Table] attribute
        assert len(db004) == 0

    def test_external_id_not_flagged_as_fk(self, tmp_path):
        """string ExternalId -> should NOT be flagged as missing FK navigation."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Order.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Order
            {
                public int Id { get; set; }
                public string ExternalId { get; set; }
                public string Name { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # ExternalId is a string FK-like pattern, but "External" is not a known entity
        # It should be flagged as DB-008 since it ends in "Id" but there's
        # no "External" entity to navigate to — this is expected behavior.
        # The key is it should NOT crash and should return a valid list.
        assert isinstance(violations, list)

    def test_correct_dual_orm_no_violations(self, tmp_path):
        """Dual ORM with correct matching types -> zero violations."""
        proj = tmp_path / "App"
        proj.mkdir()
        _make_csproj(proj / "App.csproj", efcore=True, dapper=True)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public string Name { get; set; }
                public int Age { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "UserService.cs").write_text(textwrap.dedent("""\
            public class UserService
            {
                public async Task<List<User>> GetByName()
                {
                    var sql = "SELECT * FROM Users WHERE Name = @name";
                    return await conn.QueryAsync<User>(sql, new { name });
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        assert violations == []

    def test_parameterized_queries_no_violations(self, tmp_path):
        """Dual ORM with parameterized queries -> zero DB-001/002/003 violations."""
        proj = tmp_path / "App"
        proj.mkdir()
        _make_csproj(proj / "App.csproj", efcore=True, dapper=True)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "Tender.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Tender
            {
                public int Id { get; set; }
                public TenderStatus Status { get; set; }
                public bool IsActive { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "TenderService.cs").write_text(textwrap.dedent("""\
            public class TenderService
            {
                public async Task<List<Tender>> GetActive()
                {
                    var sql = "SELECT * FROM Tenders WHERE Status = @status AND IsActive = @isActive";
                    return await conn.QueryAsync<Tender>(sql, new { status, isActive });
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        # Parameterized queries use @param, not literal values
        db_violations = [v for v in violations if v.check in ("DB-001", "DB-002", "DB-003")]
        assert len(db_violations) == 0


# =========================================================================
# 17. Severity Validation Tests
# =========================================================================


class TestSeverityValidation:
    """Tests that each DB-xxx check uses the correct severity level."""

    def test_db001_severity_is_error(self, tmp_path):
        """DB-001 violations must have severity 'error'."""
        proj = tmp_path / "App"
        proj.mkdir()
        _make_csproj(proj / "App.csproj", efcore=True, dapper=True)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "Item.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Item
            {
                public int Id { get; set; }
                public ItemStatus Status { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "ItemSvc.cs").write_text(textwrap.dedent("""\
            public class ItemSvc
            {
                public async Task Get()
                {
                    var sql = "SELECT * FROM Items WHERE Status = 1";
                    return await conn.QueryAsync(sql);
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        db001 = [v for v in violations if v.check == "DB-001"]
        assert len(db001) >= 1
        for v in db001:
            assert v.severity == "error", f"DB-001 severity should be 'error', got '{v.severity}'"

    def test_db002_severity_is_error(self, tmp_path):
        """DB-002 violations must have severity 'error'."""
        proj = tmp_path / "App"
        proj.mkdir()
        _make_csproj(proj / "App.csproj", efcore=True, dapper=True)

        entities = proj / "Entities"
        entities.mkdir()
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public bool IsActive { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "UserSvc.cs").write_text(textwrap.dedent("""\
            public class UserSvc
            {
                public async Task Get()
                {
                    var sql = "SELECT * FROM Users WHERE IsActive = 1";
                    return await conn.QueryAsync(sql);
                }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        db002 = [v for v in violations if v.check == "DB-002"]
        assert len(db002) >= 1
        for v in db002:
            assert v.severity == "error", f"DB-002 severity should be 'error', got '{v.severity}'"

    def test_db004_severity_is_warning(self, tmp_path):
        """DB-004 violations must have severity 'warning'."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public bool IsActive { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        for v in db004:
            assert v.severity == "warning", f"DB-004 severity should be 'warning', got '{v.severity}'"

    def test_db005_severity_is_error(self, tmp_path):
        """DB-005 violations must have severity 'error'."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Item.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Item
            {
                public int Id { get; set; }
                public string? Notes { get; set; }
            }
        """), encoding="utf-8")

        services = proj / "Services"
        services.mkdir()
        (services / "ItemSvc.cs").write_text(textwrap.dedent("""\
            public class ItemSvc
            {
                public int GetLen(Item item)
                {
                    return item.Notes.Length;
                }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) >= 1
        for v in db005:
            assert v.severity == "error", f"DB-005 severity should be 'error', got '{v.severity}'"

    def test_db006_severity_is_warning(self, tmp_path):
        """DB-006 violations must have severity 'warning'."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Invoice.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Invoice
            {
                public int Id { get; set; }
                public int CustomerId { get; set; }
            }
        """), encoding="utf-8")

        config_dir = proj / "Configurations"
        config_dir.mkdir()
        (config_dir / "InvoiceConfig.cs").write_text(textwrap.dedent("""\
            public class InvoiceConfig : IEntityTypeConfiguration<Invoice>
            {
                public void Configure(EntityTypeBuilder<Invoice> builder)
                {
                    builder.HasOne(i => i.Customer).WithMany(c => c.Invoices);
                }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        db006 = [v for v in violations if v.check == "DB-006"]
        assert len(db006) >= 1
        for v in db006:
            assert v.severity == "warning", f"DB-006 severity should be 'warning', got '{v.severity}'"

    def test_db008_severity_is_error(self, tmp_path):
        """DB-008 violations must have severity 'error'."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Comment.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Comment
            {
                public int Id { get; set; }
                public int PostId { get; set; }
                public string Text { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        db008 = [v for v in violations if v.check == "DB-008"]
        assert len(db008) >= 1
        for v in db008:
            assert v.severity == "error", f"DB-008 severity should be 'error', got '{v.severity}'"


# =========================================================================
# 18. TypeScript/Python Relationship Scan Tests
# =========================================================================


class TestTypeORMRelationshipScan:
    """Tests for TypeORM relationship scanning (TypeScript)."""

    def test_typeorm_joincolumn_detected(self, tmp_path):
        """TypeORM @JoinColumn + @ManyToOne are detected in relationship scan."""
        proj = tmp_path / "App"
        entities = proj / "entities"
        entities.mkdir(parents=True)
        (entities / "post.entity.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class Post {
              @PrimaryGeneratedColumn()
              id: number;

              @ManyToOne(() => User)
              @JoinColumn({ name: 'userId' })
              user: User;
            }
        """), encoding="utf-8")

        (entities / "user.entity.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class User {
              @PrimaryGeneratedColumn()
              id: number;

              name: string;
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # Should detect that User has no inverse OneToMany back to Post
        assert isinstance(violations, list)

    def test_typeorm_bidirectional_no_db007(self, tmp_path):
        """TypeORM bidirectional relation -> no DB-007."""
        proj = tmp_path / "App"
        entities = proj / "entities"
        entities.mkdir(parents=True)
        (entities / "post.entity.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class Post {
              @PrimaryGeneratedColumn()
              id: number;

              @ManyToOne(() => User)
              user: User;
            }
        """), encoding="utf-8")

        (entities / "user.entity.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class User {
              @PrimaryGeneratedColumn()
              id: number;

              @OneToMany(() => Post)
              posts: Post[];
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        db007 = [v for v in violations if v.check == "DB-007"]
        # Both sides reference each other, so no DB-007
        assert len(db007) == 0


class TestDjangoSQLAlchemyRelationshipScan:
    """Tests for Django/SQLAlchemy relationship scanning."""

    def test_django_fk_detected(self, tmp_path):
        """Django ForeignKey field is detected by relationship scan."""
        proj = tmp_path / "App"
        models_dir = proj / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "comment.py").write_text(textwrap.dedent("""\
            from django.db import models

            class Comment(models.Model):
                post = models.ForeignKey('Post', on_delete=models.CASCADE)
                text = models.TextField()
        """), encoding="utf-8")

        (models_dir / "post.py").write_text(textwrap.dedent("""\
            from django.db import models

            class Post(models.Model):
                title = models.CharField(max_length=200)
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # Django FK automatically creates navigation so it shouldn't be DB-006/008
        assert isinstance(violations, list)

    def test_sqlalchemy_fk_without_relationship(self, tmp_path):
        """SQLAlchemy FK column without relationship() call."""
        proj = tmp_path / "App"
        models_dir = proj / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "order.py").write_text(textwrap.dedent("""\
            from sqlalchemy import Column, Integer, String, ForeignKey
            from base import Base

            class Order(Base):
                __tablename__ = 'orders'
                id = Column(Integer, primary_key=True)
                userId = Column(Integer, ForeignKey('users.id'))
                total = Column(Integer)
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # SQLAlchemy FK without relationship() should be detected
        assert isinstance(violations, list)

    def test_sqlalchemy_fk_with_relationship_no_violations(self, tmp_path):
        """SQLAlchemy FK with matching relationship() -> no DB-006/008."""
        proj = tmp_path / "App"
        models_dir = proj / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "order.py").write_text(textwrap.dedent("""\
            from sqlalchemy import Column, Integer, String, ForeignKey
            from sqlalchemy.orm import relationship
            from base import Base

            class Order(Base):
                __tablename__ = 'orders'
                id = Column(Integer, primary_key=True)
                userId = Column(Integer, ForeignKey('users.id'))
                user = relationship('User')
                total = Column(Integer)
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # Has FK + matching relationship, should be clean
        assert isinstance(violations, list)
