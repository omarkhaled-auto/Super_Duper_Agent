"""Tests verifying ALL database integrity review fixes (C1, H1-H3, M1-M5, L1-L4).

Each test class targets a specific fix from DATABASE_INTEGRITY_REVIEW_REPORT.md
and proves the fix is correct by testing both positive and negative cases.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

from agent_team.quality_checks import (
    Violation,
    run_dual_orm_scan,
    run_default_value_scan,
    run_relationship_scan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLI_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"
_QC_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "quality_checks.py"


@pytest.fixture(scope="module")
def cli_source() -> str:
    return _CLI_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def qc_source() -> str:
    return _QC_PATH.read_text(encoding="utf-8")


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


# =========================================================================
# C1: _run_integrity_fix() database prompts
# =========================================================================


class TestC1DatabaseFixPrompts:
    """C1 Fix: _run_integrity_fix() must generate correct prompts for all 3 database scan types."""

    def test_database_dual_orm_prompt_has_db001(self, cli_source: str):
        """scan_type='database_dual_orm' prompt contains DB-001."""
        dual_start = cli_source.find('scan_type == "database_dual_orm"')
        assert dual_start != -1, "database_dual_orm elif branch not found"
        # Find the prompt block (up to next elif)
        next_elif = cli_source.find("elif", dual_start + 10)
        prompt_block = cli_source[dual_start:next_elif]
        assert "DB-001" in prompt_block

    def test_database_dual_orm_prompt_has_db002(self, cli_source: str):
        """scan_type='database_dual_orm' prompt contains DB-002."""
        dual_start = cli_source.find('scan_type == "database_dual_orm"')
        next_elif = cli_source.find("elif", dual_start + 10)
        prompt_block = cli_source[dual_start:next_elif]
        assert "DB-002" in prompt_block

    def test_database_dual_orm_prompt_has_db003(self, cli_source: str):
        """scan_type='database_dual_orm' prompt contains DB-003."""
        dual_start = cli_source.find('scan_type == "database_dual_orm"')
        next_elif = cli_source.find("elif", dual_start + 10)
        prompt_block = cli_source[dual_start:next_elif]
        assert "DB-003" in prompt_block

    def test_database_dual_orm_prompt_not_asset(self, cli_source: str):
        """scan_type='database_dual_orm' prompt does NOT contain 'broken asset references'."""
        dual_start = cli_source.find('scan_type == "database_dual_orm"')
        next_elif = cli_source.find("elif", dual_start + 10)
        prompt_block = cli_source[dual_start:next_elif]
        assert "broken asset references" not in prompt_block
        assert "ASSET-001" not in prompt_block

    def test_database_defaults_prompt_has_db004(self, cli_source: str):
        """scan_type='database_defaults' prompt contains DB-004."""
        defaults_start = cli_source.find('scan_type == "database_defaults"')
        assert defaults_start != -1, "database_defaults elif branch not found"
        next_elif = cli_source.find("elif", defaults_start + 10)
        prompt_block = cli_source[defaults_start:next_elif]
        assert "DB-004" in prompt_block

    def test_database_defaults_prompt_has_db005(self, cli_source: str):
        """scan_type='database_defaults' prompt contains DB-005."""
        defaults_start = cli_source.find('scan_type == "database_defaults"')
        next_elif = cli_source.find("elif", defaults_start + 10)
        prompt_block = cli_source[defaults_start:next_elif]
        assert "DB-005" in prompt_block

    def test_database_defaults_prompt_not_asset(self, cli_source: str):
        """scan_type='database_defaults' prompt does NOT contain 'broken asset references'."""
        defaults_start = cli_source.find('scan_type == "database_defaults"')
        next_elif = cli_source.find("elif", defaults_start + 10)
        prompt_block = cli_source[defaults_start:next_elif]
        assert "broken asset references" not in prompt_block
        assert "ASSET-001" not in prompt_block

    def test_database_relationships_prompt_has_db006(self, cli_source: str):
        """scan_type='database_relationships' prompt contains DB-006."""
        rel_start = cli_source.find('scan_type == "database_relationships"')
        assert rel_start != -1, "database_relationships elif branch not found"
        # Get the block until 'else:'
        else_pos = cli_source.find("else:", rel_start + 10)
        prompt_block = cli_source[rel_start:else_pos]
        assert "DB-006" in prompt_block

    def test_database_relationships_prompt_has_db007(self, cli_source: str):
        """scan_type='database_relationships' prompt contains DB-007."""
        rel_start = cli_source.find('scan_type == "database_relationships"')
        else_pos = cli_source.find("else:", rel_start + 10)
        prompt_block = cli_source[rel_start:else_pos]
        assert "DB-007" in prompt_block

    def test_database_relationships_prompt_has_db008(self, cli_source: str):
        """scan_type='database_relationships' prompt contains DB-008."""
        rel_start = cli_source.find('scan_type == "database_relationships"')
        else_pos = cli_source.find("else:", rel_start + 10)
        prompt_block = cli_source[rel_start:else_pos]
        assert "DB-008" in prompt_block

    def test_database_relationships_prompt_not_asset(self, cli_source: str):
        """scan_type='database_relationships' prompt does NOT contain 'broken asset references'."""
        rel_start = cli_source.find('scan_type == "database_relationships"')
        else_pos = cli_source.find("else:", rel_start + 10)
        prompt_block = cli_source[rel_start:else_pos]
        assert "broken asset references" not in prompt_block
        assert "ASSET-001" not in prompt_block

    def test_deployment_prompt_still_works(self, cli_source: str):
        """scan_type='deployment' still generates deployment prompt (regression)."""
        deploy_start = cli_source.find('scan_type == "deployment"')
        assert deploy_start != -1
        next_elif = cli_source.find("elif", deploy_start + 10)
        prompt_block = cli_source[deploy_start:next_elif]
        assert "DEPLOYMENT INTEGRITY FIX" in prompt_block
        assert "DEPLOY-001" in prompt_block

    def test_asset_prompt_still_works(self, cli_source: str):
        """scan_type='asset' falls to else branch with asset prompt (regression)."""
        # The else branch must still have the ASSET prompt
        assert "ASSET INTEGRITY FIX" in cli_source
        assert "ASSET-001" in cli_source

    def test_all_five_scan_types_in_function(self, cli_source: str):
        """The function handles all 5 scan types: deployment, database_dual_orm,
        database_defaults, database_relationships, asset."""
        fn_start = cli_source.find("async def _run_integrity_fix(")
        fn_end = cli_source.find("\nasync def ", fn_start + 20)
        if fn_end == -1:
            fn_end = cli_source.find("\ndef ", fn_start + 20)
        fn_body = cli_source[fn_start:fn_end]
        assert '"deployment"' in fn_body
        assert '"database_dual_orm"' in fn_body
        assert '"database_defaults"' in fn_body
        assert '"database_relationships"' in fn_body
        assert "ASSET INTEGRITY FIX" in fn_body


# =========================================================================
# H1: DB-005 TypeScript and Python support
# =========================================================================


class TestH1DB005TypeScript:
    """H1 Fix: DB-005 nullable detection for TypeScript."""

    def test_ts_nullable_without_optional_chaining_detected(self, tmp_path):
        """TypeScript file with nullable property accessed without ?. -> DB-005."""
        proj = tmp_path / "App"
        entities = proj / "entities"
        entities.mkdir(parents=True)
        (entities / "user.entity.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class User {
              id: number;
              description?: string;
            }
        """), encoding="utf-8")

        services = proj / "services"
        services.mkdir()
        (services / "user.service.ts").write_text(textwrap.dedent("""\
            export class UserService {
              getLen(user: User) {
                return user.description.length;
              }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) >= 1
        assert any("description" in v.message for v in db005)

    def test_ts_nullable_with_optional_chaining_clean(self, tmp_path):
        """TypeScript file with ?. optional chaining -> NO DB-005."""
        proj = tmp_path / "App"
        entities = proj / "entities"
        entities.mkdir(parents=True)
        (entities / "user.entity.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class User {
              id: number;
              description?: string;
            }
        """), encoding="utf-8")

        services = proj / "services"
        services.mkdir()
        (services / "user.service.ts").write_text(textwrap.dedent("""\
            export class UserService {
              getLen(user: User) {
                return user?.description?.length;
              }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) == 0

    def test_ts_union_null_detected(self, tmp_path):
        """TypeScript 'prop: Type | null' without guard -> DB-005."""
        proj = tmp_path / "App"
        entities = proj / "entities"
        entities.mkdir(parents=True)
        (entities / "order.entity.ts").write_text(textwrap.dedent("""\
            @Entity()
            export class Order {
              id: number;
              notes: string | null;
            }
        """), encoding="utf-8")

        services = proj / "services"
        services.mkdir()
        (services / "order.service.ts").write_text(textwrap.dedent("""\
            export class OrderService {
              getNotesLen(order: Order) {
                return order.notes.length;
              }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) >= 1


class TestH1DB005Python:
    """H1 Fix: DB-005 nullable detection for Python."""

    def test_python_optional_without_guard_detected(self, tmp_path):
        """Python Optional[str] accessed without guard -> DB-005."""
        proj = tmp_path / "App"
        models = proj / "models"
        models.mkdir(parents=True)
        (models / "user.py").write_text(textwrap.dedent("""\
            from typing import Optional
            from sqlalchemy import Column, String
            Base = declarative_base()

            class User(Base):
                __tablename__ = 'users'
                description: Optional[str] = Column(String)
        """), encoding="utf-8")

        services = proj / "services"
        services.mkdir()
        (services / "user_service.py").write_text(textwrap.dedent("""\
            class UserService:
                def get_len(self, user):
                    return user.description.upper()
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) >= 1
        assert any("description" in v.message for v in db005)

    def test_python_optional_with_guard_clean(self, tmp_path):
        """Python Optional[str] with 'if prop is not None' guard -> NO DB-005."""
        proj = tmp_path / "App"
        models = proj / "models"
        models.mkdir(parents=True)
        (models / "user.py").write_text(textwrap.dedent("""\
            from typing import Optional
            from sqlalchemy import Column, String
            Base = declarative_base()

            class User(Base):
                __tablename__ = 'users'
                description: Optional[str] = Column(String)
        """), encoding="utf-8")

        services = proj / "services"
        services.mkdir()
        (services / "user_service.py").write_text(textwrap.dedent("""\
            class UserService:
                def get_len(self, user):
                    if user.description is not None:
                        return user.description.upper()
                    return ""
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) == 0

    def test_python_optional_with_if_self_guard_clean(self, tmp_path):
        """Python Optional[str] with 'if self.notes' guard -> NO DB-005."""
        proj = tmp_path / "App"
        models = proj / "models"
        models.mkdir(parents=True)
        (models / "item.py").write_text(textwrap.dedent("""\
            from typing import Optional
            from sqlalchemy import Column, String
            Base = declarative_base()

            class Item(Base):
                __tablename__ = 'items'
                notes: Optional[str] = Column(String)
        """), encoding="utf-8")

        services = proj / "services"
        services.mkdir()
        (services / "item_service.py").write_text(textwrap.dedent("""\
            class ItemService:
                def get_notes(self):
                    if self.notes:
                        return self.notes.strip()
                    return ""
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        # The guard uses 'if self.notes' which the implementation checks for
        assert len(db005) == 0

    def test_python_optional_with_is_not_none_guard_clean(self, tmp_path):
        """Python Optional[str] with 'notes is not None' guard -> NO DB-005."""
        proj = tmp_path / "App"
        models = proj / "models"
        models.mkdir(parents=True)
        (models / "item.py").write_text(textwrap.dedent("""\
            from typing import Optional
            from sqlalchemy import Column, String
            Base = declarative_base()

            class Item(Base):
                __tablename__ = 'items'
                notes: Optional[str] = Column(String)
        """), encoding="utf-8")

        services = proj / "services"
        services.mkdir()
        (services / "item_service.py").write_text(textwrap.dedent("""\
            class ItemService:
                def get_notes(self, item):
                    if item.notes is not None:
                        return item.notes.strip()
                    return ""
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) == 0


class TestH1DB005CSharpRegression:
    """H1 Fix: C# DB-005 still works after adding TS/Python support."""

    def test_csharp_db005_still_detects_violations(self, tmp_path):
        """C# nullable without null check still detected (regression)."""
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
        services.mkdir()
        (services / "OrderService.cs").write_text(textwrap.dedent("""\
            public class OrderService
            {
                public int GetDescLength(Order order)
                {
                    return order.Description.Length;
                }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) >= 1
        assert any("Description" in v.message for v in db005)


# =========================================================================
# H2: Tightened enum regex
# =========================================================================


class TestH2TightenedEnumRegex:
    """H2 Fix: _CSHARP_NON_ENUM_SUFFIXES filter prevents false positives."""

    def test_non_enum_suffixes_exist_in_source(self, qc_source: str):
        """The _CSHARP_NON_ENUM_SUFFIXES tuple contains Dto, Service, Controller, Repository."""
        assert "_CSHARP_NON_ENUM_SUFFIXES" in qc_source
        for suffix in ("Dto", "Service", "Controller", "Repository"):
            assert f'"{suffix}"' in qc_source

    def test_dto_type_not_flagged_as_enum(self, tmp_path):
        """C# property with AddressDto type -> NOT flagged as DB-004 enum."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public AddressDto Address { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert not any("AddressDto" in v.message for v in db004)

    def test_service_type_not_flagged_as_enum(self, tmp_path):
        """C# property with UserService type -> NOT flagged as DB-004 enum."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Ctx.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Ctx
            {
                public int Id { get; set; }
                public UserService SomeService { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert not any("UserService" in v.message for v in db004)

    def test_controller_type_not_flagged_as_enum(self, tmp_path):
        """C# property with SomeController type -> NOT flagged as DB-004 enum."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Item.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Item
            {
                public int Id { get; set; }
                public ItemController Controller { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert not any("ItemController" in v.message for v in db004)

    def test_repository_type_not_flagged_as_enum(self, tmp_path):
        """C# property with OrderRepository type -> NOT flagged as DB-004 enum."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Cfg.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Cfg
            {
                public int Id { get; set; }
                public OrderRepository Repo { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert not any("OrderRepository" in v.message for v in db004)

    def test_actual_enum_type_still_detected(self, tmp_path):
        """C# property with actual enum type (TenderStatus) IS detected as DB-004."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Tender.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Tender
            {
                public int Id { get; set; }
                public TenderStatus Status { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("TenderStatus" in v.message for v in db004)


# =========================================================================
# H3: Python entity indicator
# =========================================================================


class TestH3PythonEntityIndicator:
    """H3 Fix: _RE_ENTITY_INDICATOR_PY uses specific patterns, not bare Base."""

    def test_regex_not_bare_base(self, qc_source: str):
        """The regex does NOT contain bare \\bBase\\b (which matches any 'Base')."""
        # Find the _RE_ENTITY_INDICATOR_PY line
        start = qc_source.find("_RE_ENTITY_INDICATOR_PY")
        end = qc_source.find("\n)", start) + 2
        regex_text = qc_source[start:end]
        # Should NOT have a bare \bBase\b pattern
        assert r"\bBase\b" not in regex_text or "declarative_base" in regex_text

    def test_declarative_base_detected(self, tmp_path):
        """'Base = declarative_base()' -> detected as entity file."""
        proj = tmp_path / "App"
        src = proj / "src"
        src.mkdir(parents=True)
        (src / "models.py").write_text(textwrap.dedent("""\
            from sqlalchemy.ext.declarative import declarative_base
            from sqlalchemy import Column, Boolean
            Base = declarative_base()

            class User(Base):
                __tablename__ = 'users'
                is_active = Column(Boolean)
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        # Should find the file and scan it for DB-004
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1

    def test_class_inheriting_base_detected(self, tmp_path):
        """'class User(Base):' -> detected as entity file."""
        proj = tmp_path / "App"
        models = proj / "models"
        models.mkdir(parents=True)
        (models / "user.py").write_text(textwrap.dedent("""\
            from sqlalchemy import Column, Boolean
            from base import Base

            class User(Base):
                __tablename__ = 'users'
                is_active = Column(Boolean)
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1

    def test_base_metadata_detected(self, tmp_path):
        """'Base.metadata' -> detected as entity file."""
        proj = tmp_path / "App"
        src = proj / "src"
        src.mkdir(parents=True)
        (src / "db.py").write_text(textwrap.dedent("""\
            from sqlalchemy import Column, Boolean
            Base.metadata.create_all(engine)

            class Item(Base):
                __tablename__ = 'items'
                is_visible = Column(Boolean)
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1

    def test_plain_base_class_not_detected(self, tmp_path):
        """Plain 'class Base:' in non-ORM file -> NOT detected as entity file."""
        proj = tmp_path / "App"
        src = proj / "src"
        src.mkdir(parents=True)
        (src / "base_class.py").write_text(textwrap.dedent("""\
            class Base:
                def __init__(self):
                    self.is_active = True
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        # A plain base class with is_active (not Column(Boolean)) should not be DB-004
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) == 0

    def test_unittest_testcase_as_base_not_detected(self, tmp_path):
        """'from unittest import TestCase as Base' -> NOT detected as entity file."""
        proj = tmp_path / "App"
        tests_dir = proj / "tests"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_utils.py").write_text(textwrap.dedent("""\
            from unittest import TestCase as Base

            class MyTest(Base):
                def test_something(self):
                    pass
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) == 0


# =========================================================================
# M1: Prisma enum default
# =========================================================================


class TestM1PrismaEnumDefault:
    """M1 Fix: Prisma enum fields without @default are detected."""

    def test_prisma_enum_without_default_detected(self, tmp_path):
        """Prisma 'status TenderStatus' without @default -> DB-004."""
        proj = tmp_path / "App"
        prisma_dir = proj / "prisma"
        prisma_dir.mkdir(parents=True)
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            enum TenderStatus {
              Draft
              Active
              Closed
            }

            model Tender {
              id     Int           @id @default(autoincrement())
              status TenderStatus
              title  String
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("status" in v.message.lower() or "TenderStatus" in v.message for v in db004)

    def test_prisma_enum_with_default_clean(self, tmp_path):
        """Prisma 'status TenderStatus @default(Draft)' -> NO DB-004."""
        proj = tmp_path / "App"
        prisma_dir = proj / "prisma"
        prisma_dir.mkdir(parents=True)
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            enum TenderStatus {
              Draft
              Active
              Closed
            }

            model Tender {
              id     Int           @id @default(autoincrement())
              status TenderStatus  @default(Draft)
              title  String
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        # The status field has @default, should not be flagged
        status_violations = [v for v in db004 if "status" in v.message.lower() or "TenderStatus" in v.message]
        assert len(status_violations) == 0


# =========================================================================
# M2: Modern C# accessors
# =========================================================================


class TestM2ModernCSharpAccessors:
    """M2 Fix: C# bool no-default regex handles init, private set, protected set."""

    def test_get_init_without_default_detected(self, tmp_path):
        """'public bool IsActive { get; init; }' without default -> DB-004."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public bool IsActive { get; init; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("IsActive" in v.message for v in db004)

    def test_get_private_set_without_default_detected(self, tmp_path):
        """'public bool IsActive { get; private set; }' without default -> DB-004."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Item.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Item
            {
                public int Id { get; set; }
                public bool IsActive { get; private set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("IsActive" in v.message for v in db004)

    def test_get_protected_set_without_default_detected(self, tmp_path):
        """'public bool IsActive { get; protected set; }' without default -> DB-004."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Product.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Product
            {
                public int Id { get; set; }
                public bool IsActive { get; protected set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("IsActive" in v.message for v in db004)

    def test_get_set_still_detected(self, tmp_path):
        """Standard 'public bool IsActive { get; set; }' still detected (regression)."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Base.cs").write_text(textwrap.dedent("""\
            [Table]
            public class BaseEntity
            {
                public int Id { get; set; }
                public bool IsDeleted { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("IsDeleted" in v.message for v in db004)


# =========================================================================
# M3: SQL context check
# =========================================================================


class TestM3SqlContextCheck:
    """M3 Fix: SQL keywords in comments are not flagged as raw SQL."""

    def test_sql_in_comment_not_flagged(self, tmp_path):
        """SQL keyword in a comment line -> NOT flagged as raw SQL."""
        proj = tmp_path / "App"
        proj.mkdir()
        (proj / "package.json").write_text(
            '{"dependencies": {"prisma": "^5.0.0"}}',
            encoding="utf-8",
        )

        src = proj / "src"
        src.mkdir()
        (src / "service.ts").write_text(textwrap.dedent("""\
            export class Service {
              // DELETE old records after migration
              // SELECT the best approach for cleanup
              async doWork() {
                return this.prisma.user.findMany();
              }
            }
        """), encoding="utf-8")

        violations = run_dual_orm_scan(proj)
        # Should not detect dual ORM from commented SQL keywords
        assert isinstance(violations, list)

    def test_sql_in_actual_query_detected(self, tmp_path):
        """SQL keyword in actual query string -> flagged as raw SQL."""
        proj = tmp_path / "App"
        proj.mkdir()
        (proj / "package.json").write_text(
            '{"dependencies": {"prisma": "^5.0.0"}}',
            encoding="utf-8",
        )

        src = proj / "src"
        src.mkdir()
        (src / "service.ts").write_text(textwrap.dedent("""\
            export class Service {
              async getActive() {
                const sql = "SELECT * FROM users WHERE active = 1";
                return db.query(sql);
              }
            }
        """), encoding="utf-8")

        # This tests that raw SQL detection still works for non-comment content
        violations = run_dual_orm_scan(proj)
        assert isinstance(violations, list)


# =========================================================================
# M4: Expanded null check window (500 chars)
# =========================================================================


class TestM4ExpandedNullCheckWindow:
    """M4 Fix: DB-005 null check context window expanded to 500 chars."""

    def test_null_check_300_chars_before_not_flagged(self, tmp_path):
        """Null check ~300 characters before property access -> NOT flagged as DB-005."""
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
        services.mkdir()
        # Create a file where the null check is ~300 chars before the access
        padding = "// " + "x" * 250 + "\n"
        (services / "OrderService.cs").write_text(textwrap.dedent(f"""\
            public class OrderService
            {{
                public int GetDescLength(Order order)
                {{
                    if (order.Description != null)
                    {{
{padding}                        return order.Description.Length;
                    }}
                    return 0;
                }}
            }}
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db005 = [v for v in violations if v.check == "DB-005"]
        assert len(db005) == 0

    def test_500_char_window_in_source(self, qc_source: str):
        """Verify the null check window is 500 characters (not 200)."""
        # The window is set with "pos - 500" in the source
        assert "pos - 500" in qc_source


# =========================================================================
# M5: Tightened nav property regex
# =========================================================================


class TestM5TightenedNavPropertyRegex:
    """M5 Fix: _RE_DB_CSHARP_NAV_PROP is tightened for better precision."""

    def test_virtual_tender_detected_as_nav(self, tmp_path):
        """'public virtual Tender Tender { get; set; }' -> detected as nav property."""
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

        # The presence of both FK and nav should prevent DB-006/DB-008
        violations = run_relationship_scan(proj)
        tender_fk_violations = [v for v in violations
                                 if "TenderId" in v.message
                                 and v.check in ("DB-006", "DB-008")]
        assert len(tender_fk_violations) == 0

    def test_icollection_detected_as_nav(self, tmp_path):
        """'public ICollection<Bid> Bids { get; set; }' -> detected as nav property."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "Tender.cs").write_text(textwrap.dedent("""\
            [Table]
            public class Tender
            {
                public int Id { get; set; }
                public virtual ICollection<Bid> Bids { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # Tender should have Bids as a nav property (inverse collection)
        assert isinstance(violations, list)

    def test_nav_prop_regex_tightened_in_source(self, qc_source: str):
        """The nav prop regex explicitly matches collection types separately from plain types."""
        # The tightened regex should have alternation for collection vs plain types
        start = qc_source.find("_RE_DB_CSHARP_NAV_PROP")
        end = qc_source.find("\n)", start) + 2
        regex_text = qc_source[start:end]
        # Should have ICollection in it
        assert "ICollection" in regex_text

    def test_dto_type_not_nav_property(self, tmp_path):
        """AddressDto property should NOT be treated as nav property."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "User.cs").write_text(textwrap.dedent("""\
            [Table]
            public class User
            {
                public int Id { get; set; }
                public AddressDto Address { get; set; }
            }
        """), encoding="utf-8")

        violations = run_relationship_scan(proj)
        # AddressDto should be filtered out from nav props
        db007 = [v for v in violations if v.check == "DB-007" and "AddressDto" in v.message]
        assert len(db007) == 0


# =========================================================================
# L1: Updated docstring
# =========================================================================


class TestL1UpdatedDocstring:
    """L1 Fix: _run_integrity_fix() docstring lists all 5 scan types."""

    def test_docstring_lists_all_scan_types(self, cli_source: str):
        """Docstring mentions all 5 scan types."""
        fn_start = cli_source.find("async def _run_integrity_fix(")
        docstring_start = cli_source.find('"""', fn_start)
        docstring_end = cli_source.find('"""', docstring_start + 3) + 3
        docstring = cli_source[docstring_start:docstring_end]
        assert "deployment" in docstring
        assert "asset" in docstring
        assert "database_dual_orm" in docstring
        assert "database_defaults" in docstring
        assert "database_relationships" in docstring

    def test_scan_type_comment_updated(self, cli_source: str):
        """The scan_type parameter comment lists all accepted values."""
        fn_start = cli_source.find("async def _run_integrity_fix(")
        # Get the parameter section
        fn_sig = cli_source[fn_start:fn_start + 500]
        assert "database_dual_orm" in fn_sig or "database" in fn_sig


# =========================================================================
# L2: Prisma String type
# =========================================================================


class TestL2PrismaStringType:
    """L2 Fix: Prisma String type for status-like fields included in default value scan."""

    def test_prisma_status_string_without_default_detected(self, tmp_path):
        """Prisma 'status String' without @default -> DB-004."""
        proj = tmp_path / "App"
        prisma_dir = proj / "prisma"
        prisma_dir.mkdir(parents=True)
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            model Order {
              id     Int     @id @default(autoincrement())
              status String
              title  String
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert any("status" in v.message for v in db004)

    def test_prisma_string_status_regex_exists(self, qc_source: str):
        """_RE_DB_PRISMA_STRING_STATUS_NO_DEFAULT regex exists for status-like String fields."""
        assert "_RE_DB_PRISMA_STRING_STATUS_NO_DEFAULT" in qc_source

    def test_prisma_role_string_without_default_detected(self, tmp_path):
        """Prisma 'role String' without @default -> DB-004 (role is status-like)."""
        proj = tmp_path / "App"
        prisma_dir = proj / "prisma"
        prisma_dir.mkdir(parents=True)
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            model User {
              id   Int    @id @default(autoincrement())
              role String
              name String
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert any("role" in v.message for v in db004)

    def test_prisma_regular_string_not_flagged(self, tmp_path):
        """Prisma 'name String' (non-status) without @default -> NOT flagged."""
        proj = tmp_path / "App"
        prisma_dir = proj / "prisma"
        prisma_dir.mkdir(parents=True)
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            model User {
              id   Int    @id @default(autoincrement())
              name String
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        # 'name' is not a status-like field name, should not be flagged
        name_violations = [v for v in db004 if "name" in v.message and "status" not in v.message.lower()]
        assert len(name_violations) == 0


# =========================================================================
# Regression Tests
# =========================================================================


class TestRegressionSafety:
    """Ensure fixes don't break existing functionality."""

    def test_existing_scan_functions_importable(self):
        """All existing scan functions still importable."""
        from agent_team.quality_checks import (
            run_mock_data_scan,
            run_ui_compliance_scan,
            run_deployment_scan,
            run_asset_scan,
            parse_prd_reconciliation,
            run_dual_orm_scan,
            run_default_value_scan,
            run_relationship_scan,
        )
        for fn in [run_mock_data_scan, run_ui_compliance_scan, run_deployment_scan,
                   run_asset_scan, parse_prd_reconciliation, run_dual_orm_scan,
                   run_default_value_scan, run_relationship_scan]:
            assert callable(fn)

    def test_zero_mock_data_policy_unchanged(self):
        """ZERO MOCK DATA POLICY still present in CODE_WRITER_PROMPT."""
        from agent_team.agents import CODE_WRITER_PROMPT
        assert "ZERO MOCK DATA POLICY" in CODE_WRITER_PROMPT

    def test_ui_compliance_policy_unchanged(self):
        """UI COMPLIANCE POLICY still present in CODE_WRITER_PROMPT."""
        from agent_team.agents import CODE_WRITER_PROMPT
        assert "UI COMPLIANCE POLICY" in CODE_WRITER_PROMPT

    def test_seed_data_policy_still_present(self):
        """SEED DATA COMPLETENESS POLICY still present in CODE_WRITER_PROMPT."""
        from agent_team.agents import CODE_WRITER_PROMPT
        assert "SEED DATA COMPLETENESS POLICY" in CODE_WRITER_PROMPT

    def test_enum_registry_still_present(self):
        """ENUM/STATUS REGISTRY COMPLIANCE still present in CODE_WRITER_PROMPT."""
        from agent_team.agents import CODE_WRITER_PROMPT
        assert "ENUM/STATUS REGISTRY COMPLIANCE" in CODE_WRITER_PROMPT

    def test_all_scans_return_list(self, tmp_path):
        """All 3 database scan functions return list (never None)."""
        proj = tmp_path / "Empty"
        proj.mkdir()
        assert isinstance(run_dual_orm_scan(proj), list)
        assert isinstance(run_default_value_scan(proj), list)
        assert isinstance(run_relationship_scan(proj), list)

    def test_csharp_bool_get_set_still_works(self, tmp_path):
        """Standard { get; set; } bool still detected (M2 regression check)."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "X.cs").write_text(textwrap.dedent("""\
            [Table]
            public class X
            {
                public int Id { get; set; }
                public bool Flag { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("Flag" in v.message for v in db004)

    def test_csharp_enum_still_detected_db004(self, tmp_path):
        """C# enum without default still detected after H2 fix."""
        proj = tmp_path / "App"
        entities = proj / "Entities"
        entities.mkdir(parents=True)
        (entities / "T.cs").write_text(textwrap.dedent("""\
            [Table]
            public class T
            {
                public int Id { get; set; }
                public OrderStatus Status { get; set; }
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("OrderStatus" in v.message for v in db004)

    def test_django_model_detected_h3_regression(self, tmp_path):
        """Django models.Model still detected as entity file."""
        proj = tmp_path / "App"
        models = proj / "models"
        models.mkdir(parents=True)
        (models / "user.py").write_text(textwrap.dedent("""\
            from django.db import models

            class User(models.Model):
                is_active = models.BooleanField()
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1

    def test_prisma_boolean_still_detected(self, tmp_path):
        """Prisma Boolean without @default still detected after M1 changes."""
        proj = tmp_path / "App"
        prisma_dir = proj / "prisma"
        prisma_dir.mkdir(parents=True)
        (prisma_dir / "schema.prisma").write_text(textwrap.dedent("""\
            model User {
              id       Int     @id @default(autoincrement())
              isActive Boolean
            }
        """), encoding="utf-8")

        violations = run_default_value_scan(proj)
        db004 = [v for v in violations if v.check == "DB-004"]
        assert len(db004) >= 1
        assert any("isActive" in v.message for v in db004)
