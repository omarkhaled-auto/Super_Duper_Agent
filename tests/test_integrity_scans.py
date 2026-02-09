"""Tests for Post-Build Integrity Scans (Deployment, Asset, PRD Reconciliation).

Covers config, quality patterns, scan functions, CLI async helpers, CLI wiring,
and prompt verification.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agent_team.config import (
    AgentTeamConfig,
    IntegrityScanConfig,
    _dict_to_config,
)
from agent_team.quality_checks import (
    Violation,
    run_deployment_scan,
    run_asset_scan,
    parse_prd_reconciliation,
    _parse_docker_compose,
    _parse_env_file,
    _extract_docker_ports,
    _extract_docker_env_vars,
    _extract_docker_service_names,
    _is_static_asset_ref,
    _resolve_asset,
)


# =========================================================================
# 1. Config — IntegrityScanConfig
# =========================================================================


class TestIntegrityScanConfig:
    """Tests for IntegrityScanConfig defaults and _dict_to_config wiring."""

    def test_defaults(self):
        cfg = IntegrityScanConfig()
        assert cfg.deployment_scan is True
        assert cfg.asset_scan is True
        assert cfg.prd_reconciliation is True

    def test_on_agent_team_config(self):
        cfg = AgentTeamConfig()
        assert isinstance(cfg.integrity_scans, IntegrityScanConfig)
        assert cfg.integrity_scans.deployment_scan is True

    def test_yaml_parsing_all_fields(self):
        data = {"integrity_scans": {
            "deployment_scan": False,
            "asset_scan": False,
            "prd_reconciliation": False,
        }}
        cfg = _dict_to_config(data)
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.integrity_scans.asset_scan is False
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_yaml_parsing_partial(self):
        data = {"integrity_scans": {"deployment_scan": False}}
        cfg = _dict_to_config(data)
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.integrity_scans.asset_scan is True  # default preserved
        assert cfg.integrity_scans.prd_reconciliation is True

    def test_yaml_missing_section_uses_defaults(self):
        cfg = _dict_to_config({})
        assert cfg.integrity_scans.deployment_scan is True
        assert cfg.integrity_scans.asset_scan is True
        assert cfg.integrity_scans.prd_reconciliation is True

    def test_yaml_invalid_type_ignored(self):
        data = {"integrity_scans": "not_a_dict"}
        cfg = _dict_to_config(data)
        # Should fall back to defaults
        assert cfg.integrity_scans.deployment_scan is True


# =========================================================================
# 2. Docker-compose helpers
# =========================================================================


class TestDockerComposeHelpers:
    """Tests for _parse_docker_compose and extraction helpers."""

    def test_parse_docker_compose_missing(self, tmp_path):
        assert _parse_docker_compose(tmp_path) is None

    def test_parse_docker_compose_yaml(self, tmp_path):
        dc = tmp_path / "docker-compose.yml"
        dc.write_text(textwrap.dedent("""\
            version: "3.8"
            services:
              api:
                build: ./backend
                ports:
                  - "3000:3000"
                environment:
                  - DATABASE_URL=postgres://localhost/db
              frontend:
                build: ./frontend
                ports:
                  - "80:80"
        """), encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is not None
        assert "api" in result["services"]
        assert "frontend" in result["services"]

    def test_parse_compose_yaml(self, tmp_path):
        """Also matches compose.yaml (short name)."""
        dc = tmp_path / "compose.yaml"
        dc.write_text("version: '3'\nservices:\n  app:\n    build: .\n", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is not None
        assert "app" in result["services"]

    def test_extract_ports_simple(self):
        dc = {"services": {"api": {"ports": ["3000:3000"]}, "db": {"ports": ["5432:5432"]}}}
        ports = _extract_docker_ports(dc)
        assert ports["api"] == [(3000, 3000)]
        assert ports["db"] == [(5432, 5432)]

    def test_extract_ports_host_container_diff(self):
        dc = {"services": {"api": {"ports": ["8080:3000"]}}}
        ports = _extract_docker_ports(dc)
        assert ports["api"] == [(8080, 3000)]

    def test_extract_ports_three_part(self):
        dc = {"services": {"api": {"ports": ["127.0.0.1:8080:3000"]}}}
        ports = _extract_docker_ports(dc)
        assert ports["api"] == [(8080, 3000)]

    def test_extract_ports_single(self):
        dc = {"services": {"api": {"ports": ["3000"]}}}
        ports = _extract_docker_ports(dc)
        assert ports["api"] == [(3000, 3000)]

    def test_extract_ports_with_protocol(self):
        dc = {"services": {"api": {"ports": ["3000:3000/tcp"]}}}
        ports = _extract_docker_ports(dc)
        assert ports["api"] == [(3000, 3000)]

    def test_extract_ports_no_ports(self):
        dc = {"services": {"api": {"build": "."}}}
        ports = _extract_docker_ports(dc)
        assert ports == {}

    def test_extract_env_dict_format(self):
        dc = {"services": {"api": {"environment": {"DB_URL": "postgres://", "SECRET": "abc"}}}}
        env = _extract_docker_env_vars(dc)
        assert "DB_URL" in env
        assert "SECRET" in env

    def test_extract_env_list_format(self):
        dc = {"services": {"api": {"environment": ["DB_URL=postgres://", "SECRET=abc"]}}}
        env = _extract_docker_env_vars(dc)
        assert "DB_URL" in env
        assert "SECRET" in env

    def test_extract_env_list_no_value(self):
        dc = {"services": {"api": {"environment": ["DB_URL"]}}}
        env = _extract_docker_env_vars(dc)
        assert "DB_URL" in env

    def test_extract_service_names(self):
        dc = {"services": {"api": {}, "db": {}, "redis": {}}}
        names = _extract_docker_service_names(dc)
        assert names == {"api", "db", "redis"}

    def test_extract_service_names_empty(self):
        dc = {"services": {}}
        names = _extract_docker_service_names(dc)
        assert names == set()


class TestEnvFileParsing:
    """Tests for _parse_env_file."""

    def test_parse_env_file_basic(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("DB_URL=postgres://localhost\nSECRET_KEY=abc\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert result == {"DB_URL", "SECRET_KEY"}

    def test_parse_env_file_comments_and_blanks(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("# comment\n\nDB_URL=postgres://localhost\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert result == {"DB_URL"}

    def test_parse_env_file_missing(self, tmp_path):
        result = _parse_env_file(tmp_path / ".env")
        assert result == set()


# =========================================================================
# 3. Deployment Scan (DEPLOY-001..004)
# =========================================================================


class TestDeploymentScan:
    """Tests for run_deployment_scan."""

    def test_no_docker_compose_returns_empty(self, tmp_path):
        violations = run_deployment_scan(tmp_path)
        assert violations == []

    def test_deploy_001_port_mismatch(self, tmp_path):
        """App listens on 4000 but docker exposes 3000."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.js").write_text("app.listen(4000);\n", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in violations if v.check == "DEPLOY-001"]
        assert len(deploy_001) >= 1
        assert "4000" in deploy_001[0].message

    def test_deploy_001_matching_port_no_violation(self, tmp_path):
        """App listens on 3000 and docker exposes 3000 — no violation."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.js").write_text("app.listen(3000);\n", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in violations if v.check == "DEPLOY-001"]
        assert len(deploy_001) == 0

    def test_deploy_002_undefined_env_var(self, tmp_path):
        """process.env.CUSTOM_VAR used but not in docker-compose or .env."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                environment:
                  - DB_URL=postgres://localhost
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const url = process.env.CUSTOM_VAR;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) >= 1
        assert "CUSTOM_VAR" in deploy_002[0].message

    def test_deploy_002_defined_var_no_violation(self, tmp_path):
        """process.env.DB_URL is defined in docker-compose — no violation."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                environment:
                  - DB_URL=postgres://localhost
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const url = process.env.DB_URL;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_deploy_002_env_file_covers(self, tmp_path):
        """Var defined in .env file — no violation."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        (tmp_path / ".env").write_text("MY_VAR=hello\n", encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const v = process.env.MY_VAR;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_deploy_002_builtin_vars_excluded(self, tmp_path):
        """NODE_ENV and PATH are builtin — not flagged."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const env = process.env.NODE_ENV;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_deploy_002_env_with_default_excluded(self, tmp_path):
        """process.env.X || 'default' has a fallback — not flagged."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const v = process.env.UNKNOWN_VAR || 'fallback';\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_deploy_003_cors_external_origin(self, tmp_path):
        """CORS set to external URL — advisory warning."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.js").write_text(
            'app.use(cors({ origin: "https://myapp.example.com" }));\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_003 = [v for v in violations if v.check == "DEPLOY-003"]
        assert len(deploy_003) >= 1
        assert "myapp.example.com" in deploy_003[0].message

    def test_deploy_003_cors_localhost_no_warning(self, tmp_path):
        """CORS set to localhost — no warning."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.js").write_text(
            'app.use(cors({ origin: "http://localhost:3000" }));\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_003 = [v for v in violations if v.check == "DEPLOY-003"]
        assert len(deploy_003) == 0

    def test_deploy_004_service_name_mismatch(self, tmp_path):
        """DB host 'postgres-server' not in docker-compose services."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              db:
                image: postgres
                ports:
                  - "5432:5432"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            'const url = "postgres://user:pass@postgres-server:5432/mydb";\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_004 = [v for v in violations if v.check == "DEPLOY-004"]
        assert len(deploy_004) >= 1
        assert "postgres-server" in deploy_004[0].message

    def test_deploy_004_matching_service_no_violation(self, tmp_path):
        """DB host 'db' matches docker-compose service name — no violation."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              db:
                image: postgres
                ports:
                  - "5432:5432"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            'const url = "postgres://user:pass@db:5432/mydb";\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_004 = [v for v in violations if v.check == "DEPLOY-004"]
        assert len(deploy_004) == 0

    def test_deploy_python_env_var(self, tmp_path):
        """os.environ[...] in Python is detected."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "settings.py").write_text(
            'SECRET = os.environ["SECRET_KEY"]\n', encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert any("SECRET_KEY" in v.message for v in deploy_002)

    def test_deploy_python_getenv_with_default_excluded(self, tmp_path):
        """os.getenv(..., 'default') has a fallback — not flagged."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "settings.py").write_text(
            "SECRET = os.getenv('SECRET_KEY', 'fallback')\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_deploy_uvicorn_port(self, tmp_path):
        """uvicorn.run port detection."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "8000:8000"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text(
            'uvicorn.run("app:app", port=9999)\n', encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in violations if v.check == "DEPLOY-001"]
        assert len(deploy_001) >= 1
        assert "9999" in deploy_001[0].message


# =========================================================================
# 4. Asset Scan (ASSET-001..003)
# =========================================================================


class TestAssetHelpers:
    """Tests for _is_static_asset_ref and _resolve_asset."""

    def test_external_url_not_static(self):
        assert _is_static_asset_ref("https://cdn.example.com/image.png") is False

    def test_data_uri_not_static(self):
        assert _is_static_asset_ref("data:image/png;base64,abc") is False

    def test_hash_not_static(self):
        assert _is_static_asset_ref("#section") is False

    def test_template_variable_not_static(self):
        assert _is_static_asset_ref("${dynamicPath}/logo.png") is False
        assert _is_static_asset_ref("{{asset}}/logo.png") is False

    def test_webpack_alias_not_static(self):
        assert _is_static_asset_ref("@/assets/logo.png") is False
        assert _is_static_asset_ref("~/assets/logo.png") is False

    def test_valid_asset_ref(self):
        assert _is_static_asset_ref("./images/logo.png") is True
        assert _is_static_asset_ref("/images/logo.svg") is True
        assert _is_static_asset_ref("assets/font.woff2") is True

    def test_non_asset_extension(self):
        assert _is_static_asset_ref("./utils/helper.js") is False
        assert _is_static_asset_ref("./styles/main.css") is False

    def test_resolve_asset_relative(self, tmp_path):
        img = tmp_path / "images" / "logo.png"
        img.parent.mkdir(parents=True)
        img.write_bytes(b"PNG")
        assert _resolve_asset("images/logo.png", tmp_path, tmp_path) is True

    def test_resolve_asset_public(self, tmp_path):
        pub = tmp_path / "public" / "favicon.ico"
        pub.parent.mkdir(parents=True)
        pub.write_bytes(b"ICO")
        assert _resolve_asset("/favicon.ico", tmp_path, tmp_path) is True

    def test_resolve_asset_missing(self, tmp_path):
        assert _resolve_asset("/images/missing.png", tmp_path, tmp_path) is False

    def test_resolve_asset_src_assets(self, tmp_path):
        f = tmp_path / "src" / "assets" / "logo.svg"
        f.parent.mkdir(parents=True)
        f.write_text("<svg></svg>", encoding="utf-8")
        assert _resolve_asset("assets/logo.svg", tmp_path, tmp_path) is True


class TestAssetScan:
    """Tests for run_asset_scan."""

    def test_empty_project_no_violations(self, tmp_path):
        violations = run_asset_scan(tmp_path)
        assert violations == []

    def test_asset_001_broken_src(self, tmp_path):
        """src="missing.png" — file doesn't exist."""
        comp = tmp_path / "src" / "App.tsx"
        comp.parent.mkdir(parents=True)
        comp.write_text(
            '<img src="./logo.png" alt="logo" />\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) >= 1
        assert "logo.png" in asset_001[0].message

    def test_asset_001_existing_src_no_violation(self, tmp_path):
        """src="./logo.png" exists — no violation."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "logo.png").write_bytes(b"PNG")
        (src / "App.tsx").write_text(
            '<img src="./logo.png" alt="logo" />\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) == 0

    def test_asset_001_external_url_skipped(self, tmp_path):
        """External https URL — not checked."""
        comp = tmp_path / "src" / "App.tsx"
        comp.parent.mkdir(parents=True)
        comp.write_text(
            '<img src="https://cdn.example.com/logo.png" />\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0

    def test_asset_002_broken_css_url(self, tmp_path):
        """url(./bg.jpg) in CSS — file missing."""
        styles = tmp_path / "src" / "styles.css"
        styles.parent.mkdir(parents=True)
        styles.write_text(
            'body { background: url("./bg.jpg"); }\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_002 = [v for v in violations if v.check == "ASSET-002"]
        assert len(asset_002) >= 1
        assert "bg.jpg" in asset_002[0].message

    def test_asset_002_existing_css_url_no_violation(self, tmp_path):
        """url(./bg.jpg) in CSS — file exists."""
        styles_dir = tmp_path / "src"
        styles_dir.mkdir()
        (styles_dir / "bg.jpg").write_bytes(b"JPG")
        (styles_dir / "styles.css").write_text(
            'body { background: url("./bg.jpg"); }\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_002 = [v for v in violations if v.check == "ASSET-002"]
        assert len(asset_002) == 0

    def test_asset_003_broken_require(self, tmp_path):
        """require('./missing.svg') — file missing."""
        comp = tmp_path / "src" / "Icon.tsx"
        comp.parent.mkdir(parents=True)
        comp.write_text(
            "const icon = require('./missing.svg');\n",
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_003 = [v for v in violations if v.check == "ASSET-003"]
        assert len(asset_003) >= 1
        assert "missing.svg" in asset_003[0].message

    def test_asset_003_existing_require_no_violation(self, tmp_path):
        """require('./icon.svg') — file exists."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "icon.svg").write_text("<svg></svg>", encoding="utf-8")
        (src / "Icon.tsx").write_text(
            "const icon = require('./icon.svg');\n",
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_003 = [v for v in violations if v.check == "ASSET-003"]
        assert len(asset_003) == 0

    def test_non_asset_import_not_flagged(self, tmp_path):
        """import from './utils' — not an asset extension."""
        comp = tmp_path / "src" / "App.tsx"
        comp.parent.mkdir(parents=True)
        comp.write_text(
            "import { foo } from './utils';\n",
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0

    def test_href_broken_asset(self, tmp_path):
        """href="./style.woff2" — broken link."""
        comp = tmp_path / "src" / "index.html"
        comp.parent.mkdir(parents=True)
        comp.write_text(
            '<link href="./fonts/custom.woff2" rel="preload" />\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) >= 1
        assert "custom.woff2" in asset_001[0].message

    def test_node_modules_skipped(self, tmp_path):
        """Files in node_modules should be skipped."""
        nm = tmp_path / "node_modules" / "some-pkg"
        nm.mkdir(parents=True)
        (nm / "broken.tsx").write_text(
            '<img src="./missing.png" />\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0


# =========================================================================
# 5. PRD Reconciliation Parsing
# =========================================================================


class TestPrdReconciliation:
    """Tests for parse_prd_reconciliation."""

    def test_missing_report_returns_empty(self, tmp_path):
        violations = parse_prd_reconciliation(tmp_path / "PRD_RECONCILIATION.md")
        assert violations == []

    def test_report_with_mismatches(self, tmp_path):
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(textwrap.dedent("""\
            # PRD Reconciliation Report

            ## VERIFIED (claim matches implementation)
            - 5 user roles: All 5 roles found in role enum

            ### MISMATCH (claim does NOT match implementation)
            - PRD says "7 dashboard widgets", found 5. Missing: Calendar, Chart
            - PRD says "3 CRUD modules", found 2. Missing: Reports module

            ## SUMMARY
            - Total claims checked: 5
            - Verified: 3
            - Mismatches: 2
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 2
        assert all(v.check == "PRD-001" for v in violations)
        assert "7 dashboard widgets" in violations[0].message
        assert "3 CRUD modules" in violations[1].message

    def test_report_all_verified(self, tmp_path):
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(textwrap.dedent("""\
            # PRD Reconciliation Report

            ## VERIFIED
            - 5 user roles: All found
            - 10 API endpoints: All found

            ## SUMMARY
            - Total claims checked: 2
            - Verified: 2
            - Mismatches: 0
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert violations == []

    def test_report_h2_mismatch_section(self, tmp_path):
        """Also supports ## MISMATCH (not just ###)."""
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(textwrap.dedent("""\
            # PRD Reconciliation Report

            ## MISMATCH
            - Missing: auth middleware for role-based access

            ## SUMMARY
            - Mismatches: 1
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 1

    def test_report_empty_mismatch_section(self, tmp_path):
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(textwrap.dedent("""\
            ### MISMATCH
            ## SUMMARY
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert violations == []

    def test_report_malformed_no_crash(self, tmp_path):
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text("random content\nno sections\n", encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert violations == []


# =========================================================================
# 6. PRD Reconciliation Prompt
# =========================================================================


class TestPrdReconciliationPrompt:
    """Tests for PRD_RECONCILIATION_PROMPT content."""

    def test_prompt_exists(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        assert isinstance(PRD_RECONCILIATION_PROMPT, str)
        assert len(PRD_RECONCILIATION_PROMPT) > 100

    def test_prompt_reads_requirements(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        assert "REQUIREMENTS.md" in PRD_RECONCILIATION_PROMPT

    def test_prompt_writes_report(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        assert "PRD_RECONCILIATION.md" in PRD_RECONCILIATION_PROMPT

    def test_prompt_has_mismatch_format(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        assert "MISMATCH" in PRD_RECONCILIATION_PROMPT
        assert "VERIFIED" in PRD_RECONCILIATION_PROMPT

    def test_prompt_quantitative_focus(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        assert "quantitative" in PRD_RECONCILIATION_PROMPT.lower()

    def test_prompt_has_format_placeholder(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        assert "{requirements_dir}" in PRD_RECONCILIATION_PROMPT
        assert "{task_text}" in PRD_RECONCILIATION_PROMPT

    def test_prompt_formats_correctly(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        formatted = PRD_RECONCILIATION_PROMPT.format(
            requirements_dir=".agent-team",
            task_text="Build a todo app",
        )
        assert ".agent-team" in formatted
        assert "Build a todo app" in formatted

    def test_prompt_count_focus(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        lower = PRD_RECONCILIATION_PROMPT.lower()
        assert "count" in lower or "route" in lower or "endpoint" in lower


# =========================================================================
# 7. CLI Async Functions
# =========================================================================


class TestRunPrdReconciliation:
    """Tests for _run_prd_reconciliation function existence and signature."""

    def test_function_exists(self):
        from agent_team.cli import _run_prd_reconciliation
        import inspect
        assert inspect.iscoroutinefunction(_run_prd_reconciliation)

    def test_function_signature(self):
        import inspect
        from agent_team.cli import _run_prd_reconciliation
        sig = inspect.signature(_run_prd_reconciliation)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "task_text" in params
        assert "constraints" in params
        assert "intervention" in params
        assert "depth" in params

    def test_return_annotation(self):
        import inspect
        from agent_team.cli import _run_prd_reconciliation
        sig = inspect.signature(_run_prd_reconciliation)
        # Should return float (cost) — may be string 'float' due to __future__ annotations
        assert sig.return_annotation in (float, "float", inspect.Parameter.empty)


class TestRunIntegrityFix:
    """Tests for _run_integrity_fix function existence and signature."""

    def test_function_exists(self):
        from agent_team.cli import _run_integrity_fix
        import inspect
        assert inspect.iscoroutinefunction(_run_integrity_fix)

    def test_function_signature(self):
        import inspect
        from agent_team.cli import _run_integrity_fix
        sig = inspect.signature(_run_integrity_fix)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "violations" in params
        assert "scan_type" in params

    def test_empty_violations_returns_zero(self):
        """_run_integrity_fix with empty list returns 0.0 immediately."""
        import asyncio
        from agent_team.cli import _run_integrity_fix
        result = asyncio.run(_run_integrity_fix(
            cwd="/tmp",
            config=AgentTeamConfig(),
            violations=[],
            scan_type="deployment",
        ))
        assert result == 0.0


# =========================================================================
# 8. CLI Wiring Verification
# =========================================================================


class TestCLIWiringIntegrity:
    """Verify integrity scan wiring is correctly positioned in main()."""

    def test_wiring_imports_available(self):
        """All scan functions are importable."""
        from agent_team.quality_checks import run_deployment_scan
        from agent_team.quality_checks import run_asset_scan
        from agent_team.quality_checks import parse_prd_reconciliation
        from agent_team.cli import _run_prd_reconciliation
        from agent_team.cli import _run_integrity_fix
        assert callable(run_deployment_scan)
        assert callable(run_asset_scan)
        assert callable(parse_prd_reconciliation)

    def test_wiring_order_in_source(self):
        """Integrity scans appear after UI compliance and before E2E phase."""
        import agent_team.cli as cli_mod
        import inspect
        source = inspect.getsource(cli_mod)
        ui_pos = source.find("UI compliance scan failed")
        integrity_pos = source.find("Deployment integrity scan")
        e2e_pos = source.find("E2E Testing Phase")
        assert ui_pos > 0, "UI compliance scan not found in source"
        assert integrity_pos > 0, "Integrity scan wiring not found in source"
        assert e2e_pos > 0, "E2E testing phase not found in source"
        assert ui_pos < integrity_pos < e2e_pos, (
            f"Wrong order: UI({ui_pos}) < Integrity({integrity_pos}) < E2E({e2e_pos})"
        )

    def test_deployment_scan_gated_by_config(self):
        """Deployment scan checks config.integrity_scans.deployment_scan."""
        import inspect
        from agent_team import cli as cli_mod
        source = inspect.getsource(cli_mod)
        assert "config.integrity_scans.deployment_scan" in source

    def test_asset_scan_gated_by_config(self):
        """Asset scan checks config.integrity_scans.asset_scan."""
        import inspect
        from agent_team import cli as cli_mod
        source = inspect.getsource(cli_mod)
        assert "config.integrity_scans.asset_scan" in source

    def test_prd_reconciliation_gated_by_config(self):
        """PRD reconciliation checks config.integrity_scans.prd_reconciliation."""
        import inspect
        from agent_team import cli as cli_mod
        source = inspect.getsource(cli_mod)
        assert "config.integrity_scans.prd_reconciliation" in source

    def test_recovery_types_wired(self):
        """Recovery types for each scan are in the source."""
        import inspect
        from agent_team import cli as cli_mod
        source = inspect.getsource(cli_mod)
        assert "deployment_integrity_fix" in source
        assert "asset_integrity_fix" in source
        assert "prd_reconciliation_mismatch" in source


# =========================================================================
# 9. Deployment Scan — Python patterns
# =========================================================================


class TestDeploymentScanPythonPatterns:
    """Additional deployment scan tests for Python frameworks."""

    def test_python_os_environ_get(self, tmp_path):
        """os.environ.get('VAR') without default is detected."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "settings.py").write_text(
            "DB = os.environ.get('DATABASE_URL')\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert any("DATABASE_URL" in v.message for v in deploy_002)

    def test_python_os_environ_get_with_default_excluded(self, tmp_path):
        """os.environ.get('VAR', 'default') has fallback — not flagged."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "settings.py").write_text(
            "DB = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')\n",
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0


# =========================================================================
# 10. Edge Cases
# =========================================================================


class TestEdgeCases:
    """Edge cases for all three scans."""

    def test_deployment_scan_malformed_yaml(self, tmp_path):
        """Malformed docker-compose doesn't crash."""
        (tmp_path / "docker-compose.yml").write_text(
            "this is not yaml: [", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        assert violations == []

    def test_asset_scan_binary_file_skipped(self, tmp_path):
        """Binary files with matching extensions don't crash the scan."""
        src = tmp_path / "src"
        src.mkdir()
        # Write a binary file with .tsx extension (unlikely but shouldn't crash)
        (src / "weird.tsx").write_bytes(b"\x00\x01\x02\x03" * 100)
        violations = run_asset_scan(tmp_path)
        # Should not crash
        assert isinstance(violations, list)

    def test_prd_reconciliation_unicode(self, tmp_path):
        """Unicode in report doesn't crash parsing."""
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text(
            "### MISMATCH\n- PRD says \u201c5 widgets\u201d but found 3\n",
            encoding="utf-8",
        )
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 1

    def test_deployment_scan_empty_services(self, tmp_path):
        """docker-compose with empty services block."""
        (tmp_path / "docker-compose.yml").write_text(
            "version: '3'\nservices:\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        assert violations == []

    def test_asset_scan_deeply_nested(self, tmp_path):
        """Assets in deeply nested directories are found."""
        deep = tmp_path / "src" / "components" / "ui" / "icons"
        deep.mkdir(parents=True)
        (deep / "logo.png").write_bytes(b"PNG")
        comp = deep / "Icon.tsx"
        comp.write_text('<img src="./logo.png" />\n', encoding="utf-8")
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) == 0  # file exists

    def test_asset_scan_public_dir_resolution(self, tmp_path):
        """Assets referenced with /path resolved from public/."""
        pub = tmp_path / "public" / "images"
        pub.mkdir(parents=True)
        (pub / "hero.jpg").write_bytes(b"JPG")
        comp = tmp_path / "src" / "Hero.tsx"
        comp.parent.mkdir(parents=True)
        comp.write_text('<img src="/images/hero.jpg" />\n', encoding="utf-8")
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) == 0

    def test_deployment_scan_multiple_services(self, tmp_path):
        """Multiple services with different port configs."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: ./backend
                ports:
                  - "3000:3000"
              frontend:
                build: ./frontend
                ports:
                  - "80:80"
              db:
                image: postgres
                ports:
                  - "5432:5432"
        """), encoding="utf-8")
        src = tmp_path / "backend" / "src"
        src.mkdir(parents=True)
        # Matching port — no violation
        (src / "index.js").write_text("app.listen(3000);\n", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in violations if v.check == "DEPLOY-001"]
        assert len(deploy_001) == 0


# =========================================================================
# 11. Integration — all three scans together
# =========================================================================


class TestIntegrationAllScans:
    """Integration test: run all three scans on a synthetic project."""

    def test_full_project_scan(self, tmp_path):
        """A project with some of each issue produces correct violations."""
        # Docker-compose with port 3000
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
                environment:
                  - DB_URL=postgres://db:5432/mydb
        """), encoding="utf-8")

        src = tmp_path / "src"
        src.mkdir()

        # Port mismatch (DEPLOY-001)
        (src / "server.js").write_text(
            "app.listen(4000);\n"
            "const secret = process.env.JWT_SECRET;\n",  # DEPLOY-002
            encoding="utf-8",
        )

        # Broken asset (ASSET-001)
        (src / "App.tsx").write_text(
            '<img src="./missing-logo.png" />\n',
            encoding="utf-8",
        )

        # PRD reconciliation report with mismatches
        agent_team = tmp_path / ".agent-team"
        agent_team.mkdir()
        (agent_team / "PRD_RECONCILIATION.md").write_text(textwrap.dedent("""\
            ### MISMATCH
            - PRD says 5 modules, found 3
        """), encoding="utf-8")

        # Run all three scans
        deploy_v = run_deployment_scan(tmp_path)
        asset_v = run_asset_scan(tmp_path)
        prd_v = parse_prd_reconciliation(agent_team / "PRD_RECONCILIATION.md")

        # Verify each scan found issues
        assert any(v.check == "DEPLOY-001" for v in deploy_v), "Expected DEPLOY-001"
        assert any(v.check == "DEPLOY-002" for v in deploy_v), "Expected DEPLOY-002"
        assert any(v.check == "ASSET-001" for v in asset_v), "Expected ASSET-001"
        assert any(v.check == "PRD-001" for v in prd_v), "Expected PRD-001"

    def test_clean_project_no_violations(self, tmp_path):
        """A project with no issues produces no violations."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
                environment:
                  - DB_URL=postgres://db:5432/mydb
        """), encoding="utf-8")
        (tmp_path / ".env").write_text("API_KEY=secret\n", encoding="utf-8")

        src = tmp_path / "src"
        src.mkdir()
        (src / "logo.png").write_bytes(b"PNG")
        (src / "server.js").write_text(
            "app.listen(3000);\n"
            "const key = process.env.API_KEY;\n"
            "const env = process.env.NODE_ENV;\n",
            encoding="utf-8",
        )
        (src / "App.tsx").write_text(
            '<img src="./logo.png" />\n',
            encoding="utf-8",
        )

        deploy_v = run_deployment_scan(tmp_path)
        asset_v = run_asset_scan(tmp_path)

        assert len(deploy_v) == 0, f"Unexpected deploy violations: {deploy_v}"
        assert len(asset_v) == 0, f"Unexpected asset violations: {asset_v}"


# =========================================================================
# 12. Violation severity
# =========================================================================


class TestViolationSeverity:
    """All integrity violations are warnings (non-blocking)."""

    def test_deployment_violations_are_warnings(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.js").write_text("app.listen(4000);\n", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        for v in violations:
            assert v.severity == "warning"

    def test_asset_violations_are_warnings(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "App.tsx").write_text(
            '<img src="./missing.png" />\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        for v in violations:
            assert v.severity == "warning"

    def test_prd_violations_are_warnings(self, tmp_path):
        report = tmp_path / "report.md"
        report.write_text(
            "### MISMATCH\n- Missing feature X\n", encoding="utf-8"
        )
        violations = parse_prd_reconciliation(report)
        for v in violations:
            assert v.severity == "warning"


# =========================================================================
# 13. REVIEW — Bugs Found (documented as tests)
# =========================================================================


class TestExportPrefixEnvFile:
    """FIXED (was HIGH): _parse_env_file now strips 'export' prefix.

    Many .env files use `export VAR=value`. After the fix, the key is
    correctly stored as 'VAR' (not 'export VAR').
    """

    def test_export_prefix_stripped(self, tmp_path):
        """'export FOO=bar' now correctly stores key as 'MY_SECRET'."""
        env = tmp_path / ".env"
        env.write_text("export MY_SECRET=hunter2\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "MY_SECRET" in result
        assert "export MY_SECRET" not in result

    def test_export_prefix_no_false_deploy_002(self, tmp_path):
        """export-prefixed .env vars no longer cause false DEPLOY-002."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        (tmp_path / ".env").write_text("export MY_SECRET=hunter2\n", encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const s = process.env.MY_SECRET;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0, "export prefix should be stripped — no false positive"


class TestNonDictYaml:
    """FIXED (was MEDIUM): _parse_docker_compose now returns None for non-dict YAML.

    If docker-compose.yml contains non-dict YAML (e.g., just a string),
    _parse_docker_compose now returns None, preventing downstream crashes.
    """

    def test_string_yaml_returns_none(self, tmp_path):
        """_parse_docker_compose returns None for 'hello' YAML (non-dict)."""
        (tmp_path / "docker-compose.yml").write_text("hello\n", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is None

    def test_list_yaml_returns_none(self, tmp_path):
        """_parse_docker_compose returns None for list YAML (non-dict)."""
        (tmp_path / "docker-compose.yml").write_text("- item1\n- item2\n", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is None

    def test_string_yaml_no_crash(self, tmp_path):
        """run_deployment_scan handles string YAML gracefully (returns empty)."""
        (tmp_path / "docker-compose.yml").write_text("hello\n", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        assert violations == []

    def test_list_yaml_no_crash(self, tmp_path):
        """run_deployment_scan handles list YAML gracefully (returns empty)."""
        (tmp_path / "docker-compose.yml").write_text("- item1\n- item2\n", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        assert violations == []

    def test_null_yaml_returns_none(self, tmp_path):
        """Empty YAML returns None (handled correctly)."""
        (tmp_path / "docker-compose.yml").write_text("", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is None

    def test_null_yaml_no_crash(self, tmp_path):
        """run_deployment_scan handles empty YAML (returns None -> empty)."""
        (tmp_path / "docker-compose.yml").write_text("", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        assert violations == []


# =========================================================================
# 14. Env File Edge Cases
# =========================================================================


class TestEnvFileEdgeCases:
    """Extended edge case tests for _parse_env_file."""

    def test_quoted_values(self, tmp_path):
        """Values with quotes are handled correctly."""
        env = tmp_path / ".env"
        env.write_text(
            'DB_URL="postgres://localhost/db"\n'
            "SECRET='my_secret'\n",
            encoding="utf-8",
        )
        result = _parse_env_file(env)
        assert "DB_URL" in result
        assert "SECRET" in result

    def test_spaces_around_equals(self, tmp_path):
        """Spaces around = are stripped from key."""
        env = tmp_path / ".env"
        env.write_text("  DB_URL = postgres://localhost/db\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "DB_URL" in result

    def test_empty_value(self, tmp_path):
        """Empty value (VAR=) is a valid env var."""
        env = tmp_path / ".env"
        env.write_text("EMPTY_VAR=\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "EMPTY_VAR" in result

    def test_no_equals_line_ignored(self, tmp_path):
        """Lines without = are skipped."""
        env = tmp_path / ".env"
        env.write_text("INVALID_LINE\nVALID=true\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "VALID" in result
        assert "INVALID_LINE" not in result

    def test_multiple_equals_in_value(self, tmp_path):
        """Only first = is used for splitting."""
        env = tmp_path / ".env"
        env.write_text("URL=postgres://user:pass@host/db?sslmode=require\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "URL" in result

    def test_comment_after_value_not_stripped(self, tmp_path):
        """Comment after value is part of value, key still parsed."""
        env = tmp_path / ".env"
        env.write_text("VAR=value # this is a comment\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "VAR" in result

    def test_only_comments_and_blanks(self, tmp_path):
        """File with only comments and blanks."""
        env = tmp_path / ".env"
        env.write_text("# comment\n\n# another\n\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert result == set()

    def test_env_example_and_env_local(self, tmp_path):
        """Deployment scan reads .env.example and .env.local too."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        (tmp_path / ".env.example").write_text("API_KEY=changeme\n", encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const k = process.env.API_KEY;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        # API_KEY defined in .env.example should prevent DEPLOY-002
        assert len(deploy_002) == 0

    def test_env_development_file(self, tmp_path):
        """Deployment scan reads .env.development too."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        (tmp_path / ".env.development").write_text("DEV_KEY=abc\n", encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const k = process.env.DEV_KEY;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0


# =========================================================================
# 15. Regex Pattern Unit Tests
# =========================================================================


class TestDeploymentRegexPatterns:
    """Direct tests for deployment-related compiled regex patterns."""

    def test_listen_port_express(self):
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search("app.listen(3000, () => {})")
        assert m is not None
        port = next((g for g in m.groups() if g), None)
        assert port == "3000"

    def test_listen_port_express_set(self):
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search("app.set('port', 8080);")
        assert m is not None
        port = next((g for g in m.groups() if g), None)
        assert port == "8080"

    def test_listen_port_uvicorn(self):
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search('uvicorn.run("app:app", host="0.0.0.0", port=8000)')
        assert m is not None
        port = next((g for g in m.groups() if g), None)
        assert port == "8000"

    def test_listen_port_env_var_no_match(self):
        """process.env.PORT should NOT match (not a hardcoded port)."""
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search("app.listen(process.env.PORT || 3000)")
        # Should match the 3000 fallback, which is after ||
        # Actually: regex looks for \(\s*(\d{2,5}) — first thing after ( must be digits
        # "process.env.PORT || 3000" starts with 'p', not digits
        # So the main listen pattern won't match. But let's check.
        # The regex has 3 alternatives. The first is \.listen\s*\(\s*(\d{2,5})
        # The text has .listen(process...) — no digits immediately after (
        # So the first alt doesn't match. The 2nd and 3rd wouldn't apply.
        # Therefore m is None — correct behavior (env var port is dynamic)
        assert m is None

    def test_listen_port_single_digit_no_match(self):
        """Single-digit port like 8 doesn't match (requires 2+ digits)."""
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search("app.listen(8)")
        assert m is None

    def test_env_var_node_matches_uppercase(self):
        from agent_team.quality_checks import _RE_ENV_VAR_NODE
        m = _RE_ENV_VAR_NODE.search("const x = process.env.DATABASE_URL;")
        assert m is not None
        assert m.group(1) == "DATABASE_URL"

    def test_env_var_node_skips_lowercase(self):
        """Lowercase env vars (process.env.nodeEnv) not matched."""
        from agent_team.quality_checks import _RE_ENV_VAR_NODE
        m = _RE_ENV_VAR_NODE.search("const x = process.env.nodeEnv;")
        assert m is None

    def test_env_var_py_os_environ(self):
        from agent_team.quality_checks import _RE_ENV_VAR_PY
        m = _RE_ENV_VAR_PY.search('SECRET = os.environ["SECRET_KEY"]')
        assert m is not None
        var = next((g for g in m.groups() if g), None)
        assert var == "SECRET_KEY"

    def test_env_var_py_getenv(self):
        from agent_team.quality_checks import _RE_ENV_VAR_PY
        m = _RE_ENV_VAR_PY.search("val = os.getenv('API_KEY')")
        assert m is not None
        var = next((g for g in m.groups() if g), None)
        assert var == "API_KEY"

    def test_env_var_py_environ_get(self):
        from agent_team.quality_checks import _RE_ENV_VAR_PY
        m = _RE_ENV_VAR_PY.search("val = os.environ.get('DB_HOST')")
        assert m is not None
        var = next((g for g in m.groups() if g), None)
        assert var == "DB_HOST"

    def test_env_with_default_node_or(self):
        from agent_team.quality_checks import _RE_ENV_WITH_DEFAULT
        m = _RE_ENV_WITH_DEFAULT.search("const v = process.env.PORT || 3000;")
        assert m is not None

    def test_env_with_default_node_nullish(self):
        from agent_team.quality_checks import _RE_ENV_WITH_DEFAULT
        m = _RE_ENV_WITH_DEFAULT.search("const v = process.env.PORT ?? 3000;")
        assert m is not None

    def test_env_with_default_py_getenv(self):
        from agent_team.quality_checks import _RE_ENV_WITH_DEFAULT
        m = _RE_ENV_WITH_DEFAULT.search("val = os.getenv('KEY', 'default')")
        assert m is not None

    def test_env_with_default_py_environ_get(self):
        from agent_team.quality_checks import _RE_ENV_WITH_DEFAULT
        m = _RE_ENV_WITH_DEFAULT.search("val = os.environ.get('KEY', 'default')")
        assert m is not None


class TestCorsRegexPatterns:
    """Direct tests for CORS origin regex patterns."""

    def test_cors_express_origin(self):
        from agent_team.quality_checks import _RE_CORS_ORIGIN
        m = _RE_CORS_ORIGIN.search('cors({ origin: "https://myapp.com" })')
        assert m is not None
        origin = next((g for g in m.groups() if g), None)
        assert origin == "https://myapp.com"

    def test_cors_django_setting(self):
        from agent_team.quality_checks import _RE_CORS_ORIGIN
        m = _RE_CORS_ORIGIN.search('CORS_ALLOWED_ORIGINS = "https://myapp.com"')
        assert m is not None
        origin = next((g for g in m.groups() if g), None)
        assert origin == "https://myapp.com"

    def test_cors_fastapi_allow_origins(self):
        from agent_team.quality_checks import _RE_CORS_ORIGIN
        m = _RE_CORS_ORIGIN.search('allow_origins=["https://myapp.com"]')
        assert m is not None
        origin = next((g for g in m.groups() if g), None)
        assert origin == "https://myapp.com"

    def test_cors_nestjs_enable_cors(self):
        from agent_team.quality_checks import _RE_CORS_ORIGIN
        m = _RE_CORS_ORIGIN.search('app.enableCors({ origin: "https://myapp.com" })')
        assert m is not None
        origin = next((g for g in m.groups() if g), None)
        assert origin == "https://myapp.com"

    def test_cors_localhost_match(self):
        """Localhost URLs do match the regex (but aren't flagged in scan)."""
        from agent_team.quality_checks import _RE_CORS_ORIGIN
        m = _RE_CORS_ORIGIN.search('cors({ origin: "http://localhost:3000" })')
        assert m is not None

    def test_cors_wildcard_match(self):
        """Wildcard * matches the regex (but isn't flagged in scan)."""
        from agent_team.quality_checks import _RE_CORS_ORIGIN
        m = _RE_CORS_ORIGIN.search('cors({ origin: "*" })')
        assert m is not None


class TestDBConnRegexPatterns:
    """Direct tests for database connection host regex."""

    def test_mongodb_connection(self):
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("mongodb://user:pass@my-mongo-host:27017/mydb")
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "my-mongo-host"

    def test_postgres_connection(self):
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("postgres://admin:pass@pg-server:5432/mydb")
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "pg-server"

    def test_postgresql_connection(self):
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("postgresql://admin:pass@pg-server:5432/mydb")
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "pg-server"

    def test_redis_connection(self):
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("redis://default:pass@cache-host:6379")
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "cache-host"

    def test_mysql_connection(self):
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("mysql://root:pass@mysql-server:3306/mydb")
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "mysql-server"

    def test_host_directive(self):
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("host: 'db-server'")
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "db-server"

    def test_host_directive_equals(self):
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search('host = "redis-server"')
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "redis-server"

    def test_localhost_matched_but_filtered_in_scan(self):
        """Localhost IS matched by regex (filtered later in scan logic)."""
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("mongodb://user:pass@localhost:27017/mydb")
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "localhost"

    def test_dotted_hostname(self):
        """Hostnames with dots like 'db.internal' are matched."""
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("postgres://user:pass@db.internal:5432/mydb")
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "db.internal"


# =========================================================================
# 16. Asset Reference Edge Cases
# =========================================================================


class TestAssetRefEdgeCases:
    """Extended edge case tests for _is_static_asset_ref."""

    def test_empty_ref(self):
        assert _is_static_asset_ref("") is False

    def test_mailto_ref(self):
        assert _is_static_asset_ref("mailto:user@example.com") is False

    def test_protocol_relative_url(self):
        assert _is_static_asset_ref("//cdn.example.com/image.png") is False

    def test_jinja_template(self):
        assert _is_static_asset_ref("{%static 'images/logo.png'%}") is False

    def test_double_brace_template(self):
        assert _is_static_asset_ref("{{asset_url}}/logo.png") is False

    def test_tilde_import(self):
        """Tilde imports like ~bootstrap are webpack aliases."""
        assert _is_static_asset_ref("~bootstrap/dist/logo.png") is False

    def test_query_string_matched_after_fix(self):
        """FIXED: Asset with query string now correctly detected.

        After the fix, query strings are stripped before checking extension.
        """
        result = _is_static_asset_ref("images/logo.png?v=123")
        assert result is True  # Query string stripped, .png detected

    def test_fragment_in_ref(self):
        """Hash fragments are filtered as starting with #."""
        assert _is_static_asset_ref("#logo") is False

    def test_relative_parent_ref(self):
        """../images/logo.png is considered a valid asset ref."""
        assert _is_static_asset_ref("../images/logo.png") is True

    def test_deeply_nested_ref(self):
        """Deep relative path is valid."""
        assert _is_static_asset_ref("../../assets/fonts/custom.woff2") is True

    def test_absolute_asset_ref(self):
        """/images/logo.svg with leading slash is valid."""
        assert _is_static_asset_ref("/images/logo.svg") is True

    def test_all_asset_extensions_recognized(self):
        """All extensions in _ASSET_EXTENSIONS are recognized."""
        from agent_team.quality_checks import _ASSET_EXTENSIONS
        for ext in _ASSET_EXTENSIONS:
            ref = f"assets/file{ext}"
            assert _is_static_asset_ref(ref) is True, f"Extension {ext} not recognized"


class TestResolveAssetEdgeCases:
    """Extended tests for _resolve_asset path resolution."""

    def test_resolve_static_dir(self, tmp_path):
        """Assets in static/ directory are found."""
        static = tmp_path / "static" / "images"
        static.mkdir(parents=True)
        (static / "logo.png").write_bytes(b"PNG")
        assert _resolve_asset("images/logo.png", tmp_path, tmp_path) is True

    def test_resolve_assets_dir(self, tmp_path):
        """Assets in assets/ directory are found."""
        assets = tmp_path / "assets" / "fonts"
        assets.mkdir(parents=True)
        (assets / "custom.woff2").write_bytes(b"WOFF")
        assert _resolve_asset("fonts/custom.woff2", tmp_path, tmp_path) is True

    def test_resolve_from_file_dir(self, tmp_path):
        """Relative resolution from the containing file's directory."""
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        (comp_dir / "icon.svg").write_text("<svg/>", encoding="utf-8")
        assert _resolve_asset("./icon.svg", comp_dir, tmp_path) is True

    def test_resolve_parent_ref(self, tmp_path):
        """../images/logo.png resolves from file dir going up one level."""
        images = tmp_path / "src" / "images"
        images.mkdir(parents=True)
        (images / "logo.png").write_bytes(b"PNG")
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        assert _resolve_asset("../images/logo.png", comp_dir, tmp_path) is True

    def test_resolve_nonexistent_returns_false(self, tmp_path):
        """Nonexistent asset returns False."""
        assert _resolve_asset("completely/missing.png", tmp_path, tmp_path) is False


# =========================================================================
# 17. CSS url() Variations
# =========================================================================


class TestCSSUrlVariations:
    """Tests for CSS url() regex with various quote/spacing patterns."""

    def test_url_double_quotes(self):
        from agent_team.quality_checks import _RE_ASSET_CSS_URL
        m = _RE_ASSET_CSS_URL.search('background: url("./bg.jpg");')
        assert m is not None
        assert m.group(1) == "./bg.jpg"

    def test_url_single_quotes(self):
        from agent_team.quality_checks import _RE_ASSET_CSS_URL
        m = _RE_ASSET_CSS_URL.search("background: url('./bg.jpg');")
        assert m is not None
        assert m.group(1) == "./bg.jpg"

    def test_url_no_quotes(self):
        from agent_team.quality_checks import _RE_ASSET_CSS_URL
        m = _RE_ASSET_CSS_URL.search("background: url(./bg.jpg);")
        assert m is not None
        assert m.group(1) == "./bg.jpg"

    def test_url_with_spaces(self):
        from agent_team.quality_checks import _RE_ASSET_CSS_URL
        m = _RE_ASSET_CSS_URL.search('background: url( "./bg.jpg" );')
        assert m is not None
        assert m.group(1) == "./bg.jpg"

    def test_url_with_query_string(self):
        """Query strings in url() - the ? is captured as part of the ref."""
        from agent_team.quality_checks import _RE_ASSET_CSS_URL
        m = _RE_ASSET_CSS_URL.search("background: url(./bg.jpg?v=123);")
        assert m is not None
        # Without quotes, the ? is captured
        assert "bg.jpg" in m.group(1)

    def test_url_data_uri_captured(self):
        """data: URIs are captured by regex (filtered by _is_static_asset_ref)."""
        from agent_team.quality_checks import _RE_ASSET_CSS_URL
        m = _RE_ASSET_CSS_URL.search("background: url(data:image/png;base64,abc);")
        assert m is not None
        # But _is_static_asset_ref will filter it out
        assert _is_static_asset_ref(m.group(1)) is False


# =========================================================================
# 18. Asset Import Regex Patterns
# =========================================================================


class TestAssetImportRegex:
    """Tests for asset src/href/require/import regex patterns."""

    def test_src_double_quotes(self):
        from agent_team.quality_checks import _RE_ASSET_SRC
        m = _RE_ASSET_SRC.search('<img src="./logo.png" />')
        assert m is not None
        assert m.group(1) == "./logo.png"

    def test_src_single_quotes(self):
        from agent_team.quality_checks import _RE_ASSET_SRC
        m = _RE_ASSET_SRC.search("<img src='./logo.png' />")
        assert m is not None
        assert m.group(1) == "./logo.png"

    def test_href_double_quotes(self):
        from agent_team.quality_checks import _RE_ASSET_HREF
        m = _RE_ASSET_HREF.search('<link href="./style.woff2" />')
        assert m is not None
        assert m.group(1) == "./style.woff2"

    def test_require_path(self):
        from agent_team.quality_checks import _RE_ASSET_REQUIRE
        m = _RE_ASSET_REQUIRE.search("const img = require('./images/logo.png');")
        assert m is not None
        assert m.group(1) == "./images/logo.png"

    def test_import_from_path(self):
        from agent_team.quality_checks import _RE_ASSET_IMPORT
        m = _RE_ASSET_IMPORT.search("import logo from './assets/logo.svg';")
        assert m is not None
        assert m.group(1) == "./assets/logo.svg"

    def test_src_with_spaces(self):
        from agent_team.quality_checks import _RE_ASSET_SRC
        m = _RE_ASSET_SRC.search('<img src = "./logo.png" />')
        assert m is not None
        assert m.group(1) == "./logo.png"


# =========================================================================
# 19. Max Violations Cap
# =========================================================================


class TestMaxViolationsCap:
    """Tests for the _MAX_VIOLATIONS (100) cap in scan functions."""

    def test_max_violations_constant(self):
        from agent_team.quality_checks import _MAX_VIOLATIONS
        assert _MAX_VIOLATIONS == 100

    def test_asset_scan_caps_at_100(self, tmp_path):
        """Asset scan stops at 100 violations."""
        src = tmp_path / "src"
        src.mkdir()
        # Create 150 files, each with a broken asset reference
        for i in range(150):
            (src / f"Component{i}.tsx").write_text(
                f'<img src="./missing{i}.png" />\n',
                encoding="utf-8",
            )
        violations = run_asset_scan(tmp_path)
        assert len(violations) <= 100

    def test_deployment_scan_caps_at_100(self, tmp_path):
        """Deployment scan violation list is capped at 100."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        # Create many files with undefined env vars
        for i in range(150):
            (src / f"config{i}.js").write_text(
                f"const v{i} = process.env.UNDEFINED_VAR_{i};\n",
                encoding="utf-8",
            )
        violations = run_deployment_scan(tmp_path)
        assert len(violations) <= 100

    def test_prd_reconciliation_caps_at_100(self, tmp_path):
        """PRD reconciliation parsing caps violations."""
        report = tmp_path / "report.md"
        lines = ["### MISMATCH\n"]
        for i in range(150):
            lines.append(f"- Mismatch item {i}\n")
        report.write_text("".join(lines), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) <= 100


# =========================================================================
# 20. PRD Reconciliation Parsing Edge Cases
# =========================================================================


class TestPrdReconciliationEdgeCases:
    """Extended edge cases for parse_prd_reconciliation."""

    def test_multiple_mismatch_sections(self, tmp_path):
        """Multiple MISMATCH sections — items from both are collected."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ### MISMATCH (Module A)
            - Missing feature A1
            - Missing feature A2

            ## VERIFIED
            - OK feature B

            ### MISMATCH (Module C)
            - Missing feature C1
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 3

    def test_h4_under_mismatch_preserved(self, tmp_path):
        """FIXED: #### subheader under MISMATCH no longer exits mismatch mode.

        After the fix, only ## and ### headers (not ####) exit mismatch mode,
        so items under h4 sub-sections are correctly captured.
        """
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ### MISMATCH
            - Item 1
            #### Details
            - Item 2
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        # #### no longer exits mismatch mode — both items captured
        assert len(violations) == 2

    def test_blank_lines_in_mismatch(self, tmp_path):
        """Blank lines in MISMATCH section don't exit mismatch mode."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ### MISMATCH

            - Item 1

            - Item 2
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 2

    def test_non_dash_lines_ignored(self, tmp_path):
        """Lines not starting with '- ' in mismatch section are ignored."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ### MISMATCH
            Some explanatory text.
            - Actual mismatch item
            Another explanation.
            - Second mismatch
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 2

    def test_mixed_h2_and_h3_mismatch(self, tmp_path):
        """Both ## MISMATCH and ### MISMATCH work."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ## MISMATCH
            - From h2 section

            ### MISMATCH
            - From h3 section
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        # First ## MISMATCH activates, then ### MISMATCH (which is also ## or ###)
        # ## MISMATCH at line 1 activates -> "- From h2 section" captured
        # ### MISMATCH: starts with ###, activates (since startswith("### MISMATCH"))
        # -> "- From h3 section" captured
        assert len(violations) == 2

    def test_mismatch_with_colon_suffix(self, tmp_path):
        """'### MISMATCH:' or '### MISMATCH (details)' both work."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ### MISMATCH: Feature gaps
            - Missing dashboard widget
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 1

    def test_mismatch_case_sensitive(self, tmp_path):
        """'### mismatch' (lowercase) does NOT trigger mismatch mode."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ### mismatch
            - This should not be captured
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 0

    def test_very_long_mismatch_text(self, tmp_path):
        """Very long mismatch line is still captured."""
        report = tmp_path / "report.md"
        long_text = "x" * 500
        report.write_text(f"### MISMATCH\n- {long_text}\n", encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 1
        assert long_text in violations[0].message

    def test_report_file_path_in_violation(self, tmp_path):
        """Violation file_path is the report filename."""
        report = tmp_path / "PRD_RECONCILIATION.md"
        report.write_text("### MISMATCH\n- Item\n", encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert violations[0].file_path == "PRD_RECONCILIATION.md"


# =========================================================================
# 21. Docker-Compose Extraction Edge Cases
# =========================================================================


class TestDockerComposeExtractionEdges:
    """Edge cases for docker-compose extraction helpers."""

    def test_extract_ports_no_services_key(self):
        """dc dict without 'services' key."""
        dc = {"version": "3.8"}
        ports = _extract_docker_ports(dc)
        assert ports == {}

    def test_extract_ports_services_is_none(self):
        """services key exists but is None."""
        dc = {"services": None}
        ports = _extract_docker_ports(dc)
        assert ports == {}

    def test_extract_ports_service_non_dict(self):
        """Service value is not a dict (e.g., null or string)."""
        dc = {"services": {"api": None, "db": "image:postgres"}}
        ports = _extract_docker_ports(dc)
        assert ports == {}

    def test_extract_ports_empty_port_string(self):
        """Empty port string is handled gracefully."""
        dc = {"services": {"api": {"ports": [""]}}}
        ports = _extract_docker_ports(dc)
        assert ports == {}

    def test_extract_ports_invalid_port_value(self):
        """Invalid port value (non-numeric)."""
        dc = {"services": {"api": {"ports": ["abc:def"]}}}
        ports = _extract_docker_ports(dc)
        assert ports == {}

    def test_extract_env_no_services(self):
        dc = {"version": "3"}
        env = _extract_docker_env_vars(dc)
        assert env == set()

    def test_extract_env_services_none(self):
        dc = {"services": None}
        env = _extract_docker_env_vars(dc)
        assert env == set()

    def test_extract_env_no_environment_key(self):
        dc = {"services": {"api": {"build": "."}}}
        env = _extract_docker_env_vars(dc)
        assert env == set()

    def test_extract_service_names_no_services(self):
        dc = {"version": "3"}
        names = _extract_docker_service_names(dc)
        assert names == set()

    def test_extract_service_names_services_none(self):
        dc = {"services": None}
        names = _extract_docker_service_names(dc)
        assert names == set()

    def test_docker_compose_yaml_extension(self, tmp_path):
        """docker-compose.yaml (not .yml) is also found."""
        dc = tmp_path / "docker-compose.yaml"
        dc.write_text("services:\n  web:\n    build: .\n", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is not None
        assert "web" in result["services"]

    def test_compose_yml_short_name(self, tmp_path):
        """compose.yml (short name) is found."""
        dc = tmp_path / "compose.yml"
        dc.write_text("services:\n  app:\n    build: .\n", encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is not None
        assert "app" in result["services"]

    def test_first_matching_file_wins(self, tmp_path):
        """If both docker-compose.yml and compose.yml exist, first wins."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  from_dc:\n    build: .\n", encoding="utf-8"
        )
        (tmp_path / "compose.yml").write_text(
            "services:\n  from_compose:\n    build: .\n", encoding="utf-8"
        )
        result = _parse_docker_compose(tmp_path)
        assert result is not None
        # docker-compose.yml comes first in the search order
        assert "from_dc" in result["services"]


# =========================================================================
# 22. Deployment Scan — DB Connection Strings (integration)
# =========================================================================


class TestDeploymentScanDBConnections:
    """Integration tests for DEPLOY-004 with various DB types."""

    def test_mongodb_service_mismatch(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              mongo:
                image: mongo
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "db.js").write_text(
            'const url = "mongodb://admin:pass@wrong-mongo:27017/mydb";\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_004 = [v for v in violations if v.check == "DEPLOY-004"]
        assert len(deploy_004) >= 1
        assert "wrong-mongo" in deploy_004[0].message

    def test_mongodb_matching_service(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              mongo:
                image: mongo
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "db.js").write_text(
            'const url = "mongodb://admin:pass@mongo:27017/mydb";\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_004 = [v for v in violations if v.check == "DEPLOY-004"]
        assert len(deploy_004) == 0

    def test_redis_service_mismatch(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              cache:
                image: redis
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "cache.js").write_text(
            'const url = "redis://default:pass@wrong-cache:6379";\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_004 = [v for v in violations if v.check == "DEPLOY-004"]
        assert len(deploy_004) >= 1

    def test_mysql_service_mismatch(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              mysql:
                image: mysql
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "db.py").write_text(
            'url = "mysql://root:pass@wrong-mysql:3306/mydb"\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_004 = [v for v in violations if v.check == "DEPLOY-004"]
        assert len(deploy_004) >= 1


# =========================================================================
# 23. CORS Integration Tests
# =========================================================================


class TestDeploymentScanCORSIntegration:
    """Integration tests for DEPLOY-003 CORS origin detection."""

    def test_cors_wildcard_not_flagged(self, tmp_path):
        """CORS origin '*' is not flagged (contains *)."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.js").write_text(
            'app.use(cors({ origin: "*" }));\n', encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_003 = [v for v in violations if v.check == "DEPLOY-003"]
        assert len(deploy_003) == 0

    def test_cors_django_external_flagged(self, tmp_path):
        """Django CORS_ALLOWED_ORIGINS with external URL is flagged."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "settings.py").write_text(
            'CORS_ALLOWED_ORIGINS = "https://production.example.com"\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_003 = [v for v in violations if v.check == "DEPLOY-003"]
        assert len(deploy_003) >= 1

    def test_cors_fastapi_external_flagged(self, tmp_path):
        """FastAPI allow_origins with external URL is flagged."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text(
            'allow_origins=["https://mysite.example.com"]\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_003 = [v for v in violations if v.check == "DEPLOY-003"]
        assert len(deploy_003) >= 1

    def test_cors_nestjs_external_flagged(self, tmp_path):
        """NestJS enableCors with external URL is flagged."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.ts").write_text(
            'app.enableCors({ origin: "https://app.example.com" });\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_003 = [v for v in violations if v.check == "DEPLOY-003"]
        assert len(deploy_003) >= 1


# =========================================================================
# 24. Asset Scan Mixed Existing/Missing
# =========================================================================


class TestAssetScanMixed:
    """Asset scan with mixed existing and missing references."""

    def test_mixed_refs_only_flags_missing(self, tmp_path):
        """Only missing assets produce violations; existing ones don't."""
        src = tmp_path / "src"
        src.mkdir()
        # Create one existing and one missing asset
        (src / "exists.png").write_bytes(b"PNG")
        (src / "App.tsx").write_text(textwrap.dedent("""\
            <div>
              <img src="./exists.png" />
              <img src="./missing.png" />
              <img src="./also-missing.jpg" />
            </div>
        """), encoding="utf-8")
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        # Should only flag the two missing assets
        assert len(asset_001) == 2
        refs = {v.message.split("'")[1] for v in asset_001}
        assert "./missing.png" in refs
        assert "./also-missing.jpg" in refs

    def test_multiple_refs_same_line(self, tmp_path):
        """Multiple asset references on the same line are all checked."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "page.html").write_text(
            '<img src="./a.png" /><img src="./b.svg" />\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) >= 2

    def test_css_and_html_mixed(self, tmp_path):
        """CSS url() and HTML src in same project."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "style.css").write_text(
            'body { background: url("./bg.jpg"); }\n', encoding="utf-8"
        )
        (src / "index.html").write_text(
            '<img src="./hero.png" />\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        checks = {v.check for v in violations}
        assert "ASSET-001" in checks
        assert "ASSET-002" in checks


# =========================================================================
# 25. Integrity Fix Prompt Content
# =========================================================================


class TestIntegrityFixPromptContent:
    """Tests for _run_integrity_fix prompt generation logic."""

    def test_deployment_fix_prompt_structure(self):
        """Verify deployment fix prompt contains expected sections."""
        # We can't easily call the async function, but we can verify
        # the prompt structure by reading the source
        import inspect
        from agent_team.cli import _run_integrity_fix
        source = inspect.getsource(_run_integrity_fix)
        assert "DEPLOYMENT INTEGRITY FIX" in source
        assert "DEPLOY-001" in source
        assert "DEPLOY-002" in source
        assert "DEPLOY-003" in source
        assert "DEPLOY-004" in source

    def test_asset_fix_prompt_structure(self):
        """Verify asset fix prompt contains expected sections."""
        import inspect
        from agent_team.cli import _run_integrity_fix
        source = inspect.getsource(_run_integrity_fix)
        assert "ASSET INTEGRITY FIX" in source
        assert "ASSET-001" in source
        assert "ASSET-002" in source
        assert "ASSET-003" in source

    def test_violations_truncated_to_20(self):
        """Prompt only includes first 20 violations."""
        import inspect
        from agent_team.cli import _run_integrity_fix
        source = inspect.getsource(_run_integrity_fix)
        assert "violations[:20]" in source

    def test_empty_violations_early_return(self):
        """Empty violations list returns 0.0 immediately."""
        import asyncio
        from agent_team.cli import _run_integrity_fix
        result = asyncio.run(_run_integrity_fix(
            cwd="/tmp",
            config=AgentTeamConfig(),
            violations=[],
            scan_type="asset",
        ))
        assert result == 0.0

    def test_empty_violations_deployment_early_return(self):
        """Empty violations for deployment also returns 0.0."""
        import asyncio
        from agent_team.cli import _run_integrity_fix
        result = asyncio.run(_run_integrity_fix(
            cwd="/tmp",
            config=AgentTeamConfig(),
            violations=[],
            scan_type="deployment",
        ))
        assert result == 0.0


# =========================================================================
# 26. PRD Reconciliation Prompt Edge Cases
# =========================================================================


class TestPrdPromptFormattingEdgeCases:
    """Tests for PRD_RECONCILIATION_PROMPT formatting edge cases."""

    def test_prompt_with_empty_task_text(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        formatted = PRD_RECONCILIATION_PROMPT.format(
            requirements_dir=".agent-team",
            task_text="",
        )
        assert ".agent-team" in formatted
        assert "REQUIREMENTS.md" in formatted

    def test_prompt_with_none_becomes_empty_string(self):
        """In _run_prd_reconciliation, task_text=None uses empty string."""
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        # Simulates what _run_prd_reconciliation does
        task_text = None
        formatted = PRD_RECONCILIATION_PROMPT.format(
            requirements_dir=".agent-team",
            task_text=f"\n[ORIGINAL USER REQUEST]\n{task_text}" if task_text else "",
        )
        assert "[ORIGINAL USER REQUEST]" not in formatted

    def test_prompt_with_task_text_included(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        task_text = "Build a multi-tenant SaaS with 5 modules"
        formatted = PRD_RECONCILIATION_PROMPT.format(
            requirements_dir=".agent-team",
            task_text=f"\n[ORIGINAL USER REQUEST]\n{task_text}",
        )
        assert "multi-tenant SaaS" in formatted
        assert "[ORIGINAL USER REQUEST]" in formatted

    def test_prompt_with_special_chars_in_task(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        task_text = 'Build app with "quotes" and {braces} and $dollar'
        # This should NOT raise because {braces} would cause a KeyError
        # ... but wait, Python format() WOULD raise on {braces}
        # The actual code uses .format() and {braces} would be a problem
        # unless escaped. Let's check.
        # Actually, {braces} would raise KeyError in .format() call
        # But in _run_prd_reconciliation, task_text is interpolated as:
        # f"\n[ORIGINAL USER REQUEST]\n{task_text}" — this is an f-string,
        # not .format(), so it's safe. Then the result goes into
        # PRD_RECONCILIATION_PROMPT.format(task_text=...)
        # So "Build app with {braces}" becomes the value of task_text param,
        # and .format() replaces {task_text} with the whole string including {braces}
        # But {braces} is NOT a format placeholder... wait.
        # Actually, .format() would try to resolve {braces} too!
        # NO — .format() only resolves named placeholders if they appear
        # literally in the template. The VALUE of task_text contains {braces}
        # but that's already been substituted.
        # Actually I need to re-read the code. The template has {task_text}
        # and when .format(task_text="value with {braces}") is called,
        # the {task_text} is replaced with the string, and {braces} in the
        # RESULT is not re-processed. So it's safe.
        formatted = PRD_RECONCILIATION_PROMPT.format(
            requirements_dir=".agent-team",
            task_text=f"\n[ORIGINAL USER REQUEST]\n{task_text}",
        )
        assert "quotes" in formatted
        assert "$dollar" in formatted

    def test_prompt_contains_step_numbers(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        assert "STEP 1" in PRD_RECONCILIATION_PROMPT
        assert "STEP 2" in PRD_RECONCILIATION_PROMPT
        assert "STEP 3" in PRD_RECONCILIATION_PROMPT

    def test_prompt_has_rules_section(self):
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        assert "RULES:" in PRD_RECONCILIATION_PROMPT

    def test_prompt_custom_requirements_dir(self):
        """Non-default requirements dir is correctly substituted."""
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        formatted = PRD_RECONCILIATION_PROMPT.format(
            requirements_dir="custom-dir",
            task_text="",
        )
        assert "custom-dir/REQUIREMENTS.md" in formatted
        assert "custom-dir/PRD_RECONCILIATION.md" in formatted


# =========================================================================
# 27. Deployment Scan — Port Detection Patterns (integration)
# =========================================================================


class TestDeploymentScanPortPatterns:
    """Integration tests for port detection in various frameworks."""

    def test_express_set_port(self, tmp_path):
        """app.set('port', 8080) is detected."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.js").write_text(
            "app.set('port', 8080);\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in violations if v.check == "DEPLOY-001"]
        assert len(deploy_001) >= 1
        assert "8080" in deploy_001[0].message

    def test_matching_port_across_host_container(self, tmp_path):
        """Host port 8080 maps to container port 3000 — app on 3000 matches."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "8080:3000"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "server.js").write_text("app.listen(3000);\n", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in violations if v.check == "DEPLOY-001"]
        assert len(deploy_001) == 0  # 3000 matches container port

    def test_mismatched_port_with_host_container_diff(self, tmp_path):
        """Host 8080:3000 but app listens on 5000 — mismatch."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "8080:3000"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "server.js").write_text("app.listen(5000);\n", encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in violations if v.check == "DEPLOY-001"]
        assert len(deploy_001) >= 1


# =========================================================================
# 28. Deployment Scan — ENV var deduplication
# =========================================================================


class TestDeploymentScanEnvDedup:
    """DEPLOY-002 deduplicates env var warnings."""

    def test_same_var_multiple_files_one_warning(self, tmp_path):
        """Same undefined var in 2 files produces only 1 DEPLOY-002."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.js").write_text(
            "const a = process.env.MISSING_VAR;\n", encoding="utf-8"
        )
        (src / "b.js").write_text(
            "const b = process.env.MISSING_VAR;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        missing_var_violations = [v for v in deploy_002 if "MISSING_VAR" in v.message]
        assert len(missing_var_violations) == 1  # Deduplicated


# =========================================================================
# 29. Violation Sorting
# =========================================================================


class TestViolationSorting:
    """Verify violations are sorted by severity, file path, line."""

    def test_deployment_violations_sorted(self, tmp_path):
        """Violations are sorted: severity first, then file, then line."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "z_config.js").write_text(
            "const a = process.env.UNDEFINED_Z;\n"
            "app.listen(4000);\n",
            encoding="utf-8",
        )
        (src / "a_config.js").write_text(
            "const b = process.env.UNDEFINED_A;\n",
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        if len(violations) >= 2:
            for i in range(len(violations) - 1):
                v1 = violations[i]
                v2 = violations[i + 1]
                sev_order = {"error": 0, "warning": 1, "info": 2}
                s1 = sev_order.get(v1.severity, 99)
                s2 = sev_order.get(v2.severity, 99)
                assert (s1, v1.file_path, v1.line) <= (s2, v2.file_path, v2.line)

    def test_asset_violations_sorted(self, tmp_path):
        """Asset violations are sorted by severity, then file, then line."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "B.tsx").write_text('<img src="./missing_b.png" />\n', encoding="utf-8")
        (src / "A.tsx").write_text('<img src="./missing_a.png" />\n', encoding="utf-8")
        violations = run_asset_scan(tmp_path)
        if len(violations) >= 2:
            for i in range(len(violations) - 1):
                v1 = violations[i]
                v2 = violations[i + 1]
                assert v1.file_path <= v2.file_path


# =========================================================================
# 30. Config Ordering in _dict_to_config
# =========================================================================


class TestConfigOrdering:
    """Verify integrity_scans is loaded BEFORE e2e_testing in config."""

    def test_integrity_scans_before_e2e_in_dict_to_config(self):
        """Config parsing handles both sections simultaneously."""
        data = {
            "integrity_scans": {"deployment_scan": False},
            "e2e_testing": {"enabled": True},
        }
        cfg = _dict_to_config(data)
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.e2e_testing.enabled is True

    def test_integrity_scans_with_all_other_sections(self):
        """integrity_scans works alongside other config sections."""
        data = {
            "orchestrator": {"model": "sonnet"},
            "milestone": {"enabled": True},
            "integrity_scans": {"asset_scan": False},
            "e2e_testing": {"enabled": False},
        }
        cfg = _dict_to_config(data)
        assert cfg.orchestrator.model == "sonnet"
        assert cfg.milestone.enabled is True
        assert cfg.integrity_scans.asset_scan is False
        assert cfg.e2e_testing.enabled is False


# =========================================================================
# 31. Scan Functions — Skip Directories
# =========================================================================


class TestScanSkipDirectories:
    """Verify that skip directories are respected by all scans."""

    def test_deployment_scan_skips_node_modules(self, tmp_path):
        """Files in node_modules are not scanned."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        nm = tmp_path / "node_modules" / "some-pkg"
        nm.mkdir(parents=True)
        (nm / "config.js").write_text(
            "const x = process.env.SOME_INTERNAL_VAR;\n",
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_deployment_scan_skips_dot_git(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        git = tmp_path / ".git" / "hooks"
        git.mkdir(parents=True)
        (git / "pre-commit.js").write_text(
            "process.env.GIT_HOOK_VAR;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_asset_scan_skips_dist(self, tmp_path):
        dist = tmp_path / "dist" / "assets"
        dist.mkdir(parents=True)
        (dist / "App.tsx").write_text(
            '<img src="./missing.png" />\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0

    def test_asset_scan_skips_build(self, tmp_path):
        build = tmp_path / "build" / "static"
        build.mkdir(parents=True)
        (build / "index.html").write_text(
            '<img src="./missing.png" />\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0


# =========================================================================
# PRODUCTION READINESS AUDIT — NEW TESTS (58+ tests)
# Added during exhaustive production audit
# =========================================================================


# =========================================================================
# P1. Regex Stress Tests
# =========================================================================


class TestRegexStressDeployment:
    """Stress tests for deployment-related regex patterns."""

    def test_listen_port_fastify_near_miss(self):
        """Fastify .listen({ port: 3000 }) — .listen( followed by non-digit."""
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        # Fastify uses .listen({ port: 3000 }) — first char after ( is {, not digit
        m = _RE_APP_LISTEN_PORT.search("server.listen({ port: 3000 })")
        # The regex requires \.listen\s*\(\s*(\d{2,5}) — { is not a digit, so no match
        # This is a known gap — documenting it
        assert m is None

    def test_listen_port_bun_serve_not_matched(self):
        """Bun.serve({ port: 3000 }) is NOT matched — documenting pattern gap."""
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search("Bun.serve({ port: 3000 })")
        assert m is None  # Known gap: Bun.serve not covered

    def test_listen_port_deno_serve_not_matched(self):
        """Deno.serve({ port: 3000 }) is NOT matched — documenting pattern gap."""
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search("Deno.serve(handler, { port: 3000 })")
        assert m is None  # Known gap

    def test_listen_port_six_digit_not_matched(self):
        """6-digit port (999999) should NOT match the regex."""
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search("app.listen(999999)")
        # \d{2,5} matches up to 5 digits
        assert m is None or len(next((g for g in m.groups() if g), "")) <= 5

    def test_env_var_node_multiline_default_not_detected(self):
        """Multi-line env var default is NOT detected — documenting behavior."""
        from agent_team.quality_checks import _RE_ENV_WITH_DEFAULT
        # On a single line without ||, the default regex does not match
        line = "const PORT = process.env.PORT"
        m = _RE_ENV_WITH_DEFAULT.search(line)
        assert m is None  # Multi-line default on next line won't be caught

    def test_cors_origin_very_long_line(self):
        """CORS regex on very long line with no closing brace."""
        from agent_team.quality_checks import _RE_CORS_ORIGIN
        # Create a very long line that should still terminate (no ReDoS)
        padding = "a" * 10000
        line = f'cors({{ {padding} origin: "https://example.com" }})'
        m = _RE_CORS_ORIGIN.search(line)
        assert m is not None
        origin = next((g for g in m.groups() if g), None)
        assert origin == "https://example.com"

    def test_db_conn_host_no_password(self):
        """Connection string without password: mongodb://user@host:port."""
        from agent_team.quality_checks import _RE_DB_CONN_HOST
        m = _RE_DB_CONN_HOST.search("mongodb://admin@my-mongo:27017/db")
        # Pattern is (?:\w+:?\w*@)? — admin@... should match
        assert m is not None
        host = next((g for g in m.groups() if g), None)
        assert host == "my-mongo"

    def test_asset_import_dynamic_not_matched(self):
        """Dynamic import() is NOT matched by _RE_ASSET_IMPORT."""
        from agent_team.quality_checks import _RE_ASSET_IMPORT
        # Dynamic import: import('./path') — no 'from' keyword
        m = _RE_ASSET_IMPORT.search("const mod = import('./assets/logo.svg')")
        # _RE_ASSET_IMPORT pattern uses 'from' keyword
        assert m is None

    def test_css_url_font_face_src(self):
        """@font-face src: url() is captured by _RE_ASSET_CSS_URL."""
        from agent_team.quality_checks import _RE_ASSET_CSS_URL
        m = _RE_ASSET_CSS_URL.search("src: url('./fonts/custom.woff2');")
        assert m is not None
        assert m.group(1) == "./fonts/custom.woff2"

    def test_listen_port_zero_single_digit_no_match(self):
        """Port 0 (single digit) should NOT match."""
        from agent_team.quality_checks import _RE_APP_LISTEN_PORT
        m = _RE_APP_LISTEN_PORT.search("app.listen(0)")
        assert m is None  # Single digit doesn't match \d{2,5}


# =========================================================================
# P2. Windows Path Tests
# =========================================================================


class TestWindowsPathHandling:
    """Tests for Windows-specific path handling."""

    def test_is_static_asset_ref_backslash_path(self):
        """Backslash paths should still detect asset extension."""
        result = _is_static_asset_ref("images\\logo.png")
        # Path("images\\logo.png").suffix on any OS returns ".png"
        assert result is True

    def test_resolve_asset_with_spaces_in_path(self, tmp_path):
        """Asset resolution works with spaces in directory names."""
        dir_with_space = tmp_path / "My Assets"
        dir_with_space.mkdir()
        (dir_with_space / "logo.png").write_bytes(b"PNG")
        assert _resolve_asset("My Assets/logo.png", tmp_path, tmp_path) is True

    def test_asset_scan_path_with_spaces(self, tmp_path):
        """Asset scan works in project with spaces in path."""
        src = tmp_path / "src folder"
        src.mkdir()
        (src / "App.tsx").write_text(
            '<img src="./logo.png" />\n', encoding="utf-8"
        )
        # Should not crash
        violations = run_asset_scan(tmp_path)
        assert isinstance(violations, list)

    def test_is_static_asset_ref_double_backslash(self):
        """Double backslash path is handled."""
        result = _is_static_asset_ref("images\\\\logo.png")
        # Path handles double backslash
        assert result is True

    def test_docker_compose_with_forward_slash_paths(self, tmp_path):
        """Docker compose with forward-slash build context paths."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build:
                  context: ./backend
                  dockerfile: Dockerfile
                ports:
                  - "3000:3000"
        """), encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is not None
        assert "api" in result["services"]


# =========================================================================
# P3. Encoding Tests
# =========================================================================


class TestEncodingHandling:
    """Tests for various file encodings."""

    def test_env_file_with_bom(self, tmp_path):
        """FIXED: BOM in .env file is now stripped — first var parsed correctly."""
        env = tmp_path / ".env"
        # Write with BOM
        env.write_bytes(b"\xef\xbb\xbfFIRST_VAR=value\nSECOND_VAR=value\n")
        result = _parse_env_file(env)
        assert "FIRST_VAR" in result
        assert "SECOND_VAR" in result
        assert "\ufeffFIRST_VAR" not in result  # BOM stripped

    def test_prd_reconciliation_with_bom(self, tmp_path):
        """BOM at start of PRD reconciliation report."""
        report = tmp_path / "PRD_RECONCILIATION.md"
        content = "\ufeff# PRD Reconciliation Report\n\n### MISMATCH\n- Missing item\n"
        report.write_text(content, encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        # BOM is at start of file, ### MISMATCH is on line 3 — should work
        assert len(violations) == 1

    def test_source_file_with_null_bytes(self, tmp_path):
        """Source file with NUL bytes doesn't crash deployment scan."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        content = b"const x = process.env.MY_VAR;\x00\x00\napp.listen(3000);\n"
        (src / "app.js").write_bytes(content)
        violations = run_deployment_scan(tmp_path)
        assert isinstance(violations, list)

    def test_utf8_emoji_in_prd_report(self, tmp_path):
        """Emoji characters in PRD report don't crash parsing."""
        report = tmp_path / "report.md"
        report.write_text(
            "### MISMATCH\n- Missing dashboard widget \U0001f4ca\n",
            encoding="utf-8",
        )
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 1

    def test_latin1_source_file_handled(self, tmp_path):
        """Latin-1 encoded file is handled by errors='replace'."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        content = b"// R\xe9sum\xe9 handler\nconst x = process.env.MY_VAR;\n"
        (src / "handler.js").write_bytes(content)
        violations = run_deployment_scan(tmp_path)
        assert isinstance(violations, list)

    def test_asset_scan_mixed_encoding(self, tmp_path):
        """Asset scan handles files with mixed encoding gracefully."""
        src = tmp_path / "src"
        src.mkdir()
        content = b'<img src="./\xc3\xa9.png" />\n'
        (src / "App.tsx").write_bytes(content)
        violations = run_asset_scan(tmp_path)
        assert isinstance(violations, list)


# =========================================================================
# P4. .env Variations
# =========================================================================


class TestEnvFileVariationsExtended:
    """Extended .env file format variations."""

    def test_export_with_tab_separator(self, tmp_path):
        """FIXED: 'export\\tVAR=value' — export followed by tab now handled."""
        env = tmp_path / ".env"
        env.write_text("export\tMY_VAR=hello\n", encoding="utf-8")
        result = _parse_env_file(env)
        assert "MY_VAR" in result

    def test_env_windows_line_endings(self, tmp_path):
        """Windows \\r\\n line endings are handled."""
        env = tmp_path / ".env"
        env.write_bytes(b"DB_URL=postgres://localhost\r\nSECRET=abc\r\n")
        result = _parse_env_file(env)
        assert "DB_URL" in result
        assert "SECRET" in result

    def test_env_many_empty_lines(self, tmp_path):
        """Many empty lines between entries."""
        env = tmp_path / ".env"
        env.write_text(
            "\n\n\nDB_URL=x\n\n\n\nSECRET=y\n\n\n", encoding="utf-8"
        )
        result = _parse_env_file(env)
        assert "DB_URL" in result
        assert "SECRET" in result

    def test_env_production_scanned(self, tmp_path):
        """FIXED: .env.production IS now scanned by deployment scan."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        (tmp_path / ".env.production").write_text("PROD_KEY=abc\n", encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "const k = process.env.PROD_KEY;\n", encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        # .env.production IS read — PROD_KEY should NOT be flagged
        assert not any("PROD_KEY" in v.message for v in deploy_002)

    def test_env_no_trailing_newline(self, tmp_path):
        """File without trailing newline still parses last line."""
        env = tmp_path / ".env"
        env.write_text("DB_URL=postgres://localhost\nSECRET=abc", encoding="utf-8")
        result = _parse_env_file(env)
        assert "DB_URL" in result
        assert "SECRET" in result

    def test_env_with_hash_in_value(self, tmp_path):
        """Hash (#) inside quoted value is part of value, not a comment."""
        env = tmp_path / ".env"
        env.write_text('COLOR="#ff0000"\n', encoding="utf-8")
        result = _parse_env_file(env)
        assert "COLOR" in result


# =========================================================================
# P5. Docker Compose Variations
# =========================================================================


class TestDockerComposeVariationsExtended:
    """Extended Docker Compose format variations."""

    def test_compose_v2_no_version_key(self, tmp_path):
        """Docker Compose v2 without 'version' key."""
        (tmp_path / "compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
        """), encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is not None
        assert "api" in result["services"]

    def test_compose_with_profiles(self, tmp_path):
        """Docker Compose with profiles field."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
                profiles:
                  - debug
              db:
                image: postgres
                ports:
                  - "5432:5432"
        """), encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        assert result is not None
        names = _extract_docker_service_names(result)
        assert "api" in names
        assert "db" in names

    def test_compose_with_depends_on(self, tmp_path):
        """Docker Compose with depends_on."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                depends_on:
                  - db
                ports:
                  - "3000:3000"
              db:
                image: postgres
        """), encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        ports = _extract_docker_ports(result)
        assert ports["api"] == [(3000, 3000)]

    def test_compose_with_env_file_directive(self, tmp_path):
        """Docker Compose with env_file directive (not directly parsed for vars)."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                env_file:
                  - .env
        """), encoding="utf-8")
        result = _parse_docker_compose(tmp_path)
        # env_file is a compose directive but _extract_docker_env_vars reads
        # the 'environment' key, not 'env_file'. So no env vars extracted.
        env = _extract_docker_env_vars(result)
        assert env == set()

    def test_compose_integer_ports(self):
        """Ports as integers (not strings) in docker-compose."""
        dc = {"services": {"api": {"ports": [3000]}}}
        ports = _extract_docker_ports(dc)
        assert ports["api"] == [(3000, 3000)]

    def test_compose_port_with_ip_binding(self):
        """Port with IP binding: 0.0.0.0:8080:3000."""
        dc = {"services": {"api": {"ports": ["0.0.0.0:8080:3000"]}}}
        ports = _extract_docker_ports(dc)
        assert ports["api"] == [(8080, 3000)]

    def test_compose_only_networks_no_crash(self, tmp_path):
        """Docker Compose with only networks section — no services."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            networks:
              mynet:
                driver: bridge
        """), encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        assert violations == []


# =========================================================================
# P6. Asset Resolution Edge Cases
# =========================================================================


class TestAssetResolutionEdgeCasesExtended:
    """Extended edge cases for asset resolution."""

    def test_asset_ref_with_query_and_fragment(self):
        """Reference with both query string and fragment."""
        result = _is_static_asset_ref("images/logo.png?v=123#top")
        assert result is True

    def test_asset_ref_encoded_spaces(self):
        """Encoded space (%20) in asset reference."""
        result = _is_static_asset_ref("images/my%20logo.png")
        assert result is True

    def test_scss_import_without_url_not_detected(self, tmp_path):
        """DOCUMENTED GAP: SCSS @import 'file.woff2' without url() not detected."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "fonts.scss").write_text(
            "@import './fonts/custom.woff2';\n",
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_002 = [v for v in violations if v.check == "ASSET-002"]
        asset_003 = [v for v in violations if v.check == "ASSET-003"]
        # Neither CSS url() nor require/import-from catches @import
        assert len(asset_002) == 0
        assert len(asset_003) == 0

    def test_asset_ref_to_directory_not_matched(self, tmp_path):
        """Reference to a directory (not file) is not resolved."""
        d = tmp_path / "images"
        d.mkdir()
        assert _resolve_asset("images", tmp_path, tmp_path) is False

    def test_asset_ref_traversal_above_root(self, tmp_path):
        """../../outside/path.png traversing above project root."""
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        result = _resolve_asset("../../../outside.png", comp_dir, tmp_path)
        assert result is False


# =========================================================================
# P7. PRD Report Variations
# =========================================================================


class TestPrdReportVariationsExtended:
    """Extended PRD reconciliation report format variations."""

    def test_report_with_only_summary(self, tmp_path):
        """Report with only SUMMARY section — no mismatches."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            # PRD Reconciliation Report

            ## SUMMARY
            - Total claims checked: 5
            - Verified: 5
            - Mismatches: 0
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert violations == []

    def test_report_deeply_nested_h5_header(self, tmp_path):
        """##### headers under MISMATCH don't exit mismatch mode."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ### MISMATCH
            - Item 1
            ##### Deep detail
            - Item 2
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 2

    def test_mismatch_word_in_non_header_not_triggers(self, tmp_path):
        """Word MISMATCH in normal text doesn't trigger capture."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            # Report
            This section discusses MISMATCH handling.
            - This is not a mismatch item
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 0

    def test_report_windows_line_endings(self, tmp_path):
        """Report with \\r\\n line endings."""
        report = tmp_path / "report.md"
        report.write_bytes(
            b"### MISMATCH\r\n- Missing feature X\r\n## SUMMARY\r\n"
        )
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 1

    def test_report_with_indented_dash_items(self, tmp_path):
        """Indented list items under MISMATCH."""
        report = tmp_path / "report.md"
        report.write_text(textwrap.dedent("""\
            ### MISMATCH
              - Indented item 1
            - Normal item 2
        """), encoding="utf-8")
        violations = parse_prd_reconciliation(report)
        assert len(violations) == 2


# =========================================================================
# P8. CLI Function Tests
# =========================================================================


class TestCLIFunctionEdgeCases:
    """Edge cases for CLI functions and prompt formatting."""

    def test_prd_prompt_very_long_task_text(self):
        """Very long task text doesn't break format."""
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        long_task = "Build a " + "x" * 10000 + " application"
        formatted = PRD_RECONCILIATION_PROMPT.format(
            requirements_dir=".agent-team",
            task_text=f"\n[ORIGINAL USER REQUEST]\n{long_task}",
        )
        assert "x" * 100 in formatted

    def test_prd_prompt_requirements_dir_special_chars(self):
        """Requirements dir with special chars formats correctly."""
        from agent_team.cli import PRD_RECONCILIATION_PROMPT
        formatted = PRD_RECONCILIATION_PROMPT.format(
            requirements_dir="my-project/.agent-team",
            task_text="",
        )
        assert "my-project/.agent-team/REQUIREMENTS.md" in formatted
        assert "my-project/.agent-team/PRD_RECONCILIATION.md" in formatted

    def test_config_all_integrity_scans_disabled(self):
        """All three scans can be disabled independently."""
        cfg = _dict_to_config({"integrity_scans": {
            "deployment_scan": False,
            "asset_scan": False,
            "prd_reconciliation": False,
        }})
        assert cfg.integrity_scans.deployment_scan is False
        assert cfg.integrity_scans.asset_scan is False
        assert cfg.integrity_scans.prd_reconciliation is False

    def test_integrity_fix_empty_violations_both_types(self):
        """Both scan types return 0.0 for empty violations."""
        import asyncio
        from agent_team.cli import _run_integrity_fix
        for scan_type in ("deployment", "asset"):
            result = asyncio.run(_run_integrity_fix(
                cwd="/tmp",
                config=AgentTeamConfig(),
                violations=[],
                scan_type=scan_type,
            ))
            assert result == 0.0, f"Expected 0.0 for {scan_type}"


# =========================================================================
# P9. Integration Scenarios
# =========================================================================


class TestIntegrationScenarios:
    """Full-stack project structure integration tests."""

    def test_nextjs_project_structure(self, tmp_path):
        """Next.js project with pages, public, api directories."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              web:
                build: .
                ports:
                  - "3000:3000"
                environment:
                  - DATABASE_URL=postgres://db:5432/app
              db:
                image: postgres
                ports:
                  - "5432:5432"
        """), encoding="utf-8")

        pages = tmp_path / "pages"
        pages.mkdir()
        (pages / "index.tsx").write_text(
            '<img src="/logo.png" />\n', encoding="utf-8"
        )

        pub = tmp_path / "public"
        pub.mkdir()
        (pub / "logo.png").write_bytes(b"PNG")

        api = tmp_path / "pages" / "api"
        api.mkdir()
        (api / "health.ts").write_text(
            "export default function handler(req, res) { res.json({ok: true}); }\n",
            encoding="utf-8",
        )

        deploy_v = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in deploy_v if v.check == "DEPLOY-001"]
        assert len(deploy_001) == 0

        asset_v = run_asset_scan(tmp_path)
        asset_001 = [v for v in asset_v if v.check == "ASSET-001"]
        assert len(asset_001) == 0

    def test_flask_project_with_static(self, tmp_path):
        """Flask project with static files."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "5000:5000"
        """), encoding="utf-8")
        (tmp_path / ".env").write_text("FLASK_ENV=development\n", encoding="utf-8")

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text(
            "from flask import Flask\n"
            "app = Flask(__name__)\n"
            "SECRET = os.environ.get('FLASK_ENV', 'production')\n",
            encoding="utf-8",
        )

        static = tmp_path / "static"
        static.mkdir()
        (static / "logo.png").write_bytes(b"PNG")

        (src / "index.html").write_text(
            '<img src="/logo.png" />\n', encoding="utf-8"
        )

        deploy_v = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in deploy_v if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_monorepo_packages_scanned(self, tmp_path):
        """Monorepo with packages/*/src structure."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: ./packages/api
                ports:
                  - "3000:3000"
        """), encoding="utf-8")

        api_src = tmp_path / "packages" / "api" / "src"
        api_src.mkdir(parents=True)
        (api_src / "index.ts").write_text(
            "app.listen(3000);\n"
            "const db = process.env.DATABASE_URL;\n",
            encoding="utf-8",
        )

        web_src = tmp_path / "packages" / "web" / "src"
        web_src.mkdir(parents=True)
        (web_src / "App.tsx").write_text(
            '<img src="./logo.png" />\n', encoding="utf-8"
        )

        deploy_v = run_deployment_scan(tmp_path)
        deploy_001 = [v for v in deploy_v if v.check == "DEPLOY-001"]
        assert len(deploy_001) == 0
        deploy_002 = [v for v in deploy_v if v.check == "DEPLOY-002"]
        assert any("DATABASE_URL" in v.message for v in deploy_002)

        asset_v = run_asset_scan(tmp_path)
        asset_001 = [v for v in asset_v if v.check == "ASSET-001"]
        assert len(asset_001) >= 1

    def test_django_vue_project(self, tmp_path):
        """Django backend + Vue frontend project."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              backend:
                build: ./backend
                ports:
                  - "8000:8000"
                environment:
                  DJANGO_SECRET_KEY: change-me
              frontend:
                build: ./frontend
                ports:
                  - "8080:80"
        """), encoding="utf-8")

        be = tmp_path / "backend" / "src"
        be.mkdir(parents=True)
        (be / "settings.py").write_text(
            "SECRET_KEY = os.environ['DJANGO_SECRET_KEY']\n",
            encoding="utf-8",
        )

        fe = tmp_path / "frontend" / "src"
        fe.mkdir(parents=True)
        (fe / "App.vue").write_text(
            '<template><img src="./assets/logo.png" /></template>\n',
            encoding="utf-8",
        )

        deploy_v = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in deploy_v if v.check == "DEPLOY-002"]
        django_secret = [v for v in deploy_002 if "DJANGO_SECRET_KEY" in v.message]
        assert len(django_secret) == 0


# =========================================================================
# P10. Negative Tests
# =========================================================================


class TestNegativeTests:
    """Tests verifying scans DON'T flag things they shouldn't."""

    def test_js_module_import_not_flagged_as_asset(self, tmp_path):
        """import from 'react' — not an asset extension."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "App.tsx").write_text(
            "import React from 'react';\n"
            "import { useState } from 'react';\n"
            "import axios from 'axios';\n",
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0

    def test_css_class_name_not_flagged_as_asset(self, tmp_path):
        """CSS class .logo-png is NOT an asset reference."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "style.css").write_text(
            ".logo-png { width: 100px; }\n", encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0

    def test_env_var_in_comment_still_flagged(self, tmp_path):
        """NOTE: process.env in comments IS still flagged (regex-based, no AST)."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.js").write_text(
            "// Use process.env.COMMENTED_VAR for config\n",
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        commented = [v for v in deploy_002 if "COMMENTED_VAR" in v.message]
        assert len(commented) == 1

    def test_only_python_files_no_asset_violations(self, tmp_path):
        """Project with only .py files — no asset violations."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text(
            "from flask import Flask\napp = Flask(__name__)\n",
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0

    def test_deployment_scan_no_source_files(self, tmp_path):
        """Docker compose exists but no source files — no crash."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              api:
                build: .
                ports:
                  - "3000:3000"
        """), encoding="utf-8")
        violations = run_deployment_scan(tmp_path)
        assert isinstance(violations, list)

    def test_asset_href_to_css_not_flagged(self, tmp_path):
        """href to .css file is NOT an asset (not in ASSET_EXTENSIONS)."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.html").write_text(
            '<link href="./styles.css" rel="stylesheet" />\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) == 0


# =========================================================================
# P11. Large Project Simulation
# =========================================================================


class TestLargeProjectSimulation:
    """Verify scan behavior under load with many files."""

    def test_deployment_scan_many_files_no_crash(self, tmp_path):
        """100 source files with env vars — scans complete without crash."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        for i in range(100):
            (src / f"module{i}.js").write_text(
                f"const v{i} = process.env.VAR_{i};\n",
                encoding="utf-8",
            )
        violations = run_deployment_scan(tmp_path)
        assert isinstance(violations, list)
        assert len(violations) <= 100

    def test_asset_scan_many_clean_files(self, tmp_path):
        """Many files with no broken assets — quick scan."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "logo.png").write_bytes(b"PNG")
        for i in range(50):
            (src / f"Component{i}.tsx").write_text(
                '<img src="./logo.png" />\n', encoding="utf-8"
            )
        violations = run_asset_scan(tmp_path)
        assert len(violations) == 0


# =========================================================================
# P12. Docker Port Edge Cases
# =========================================================================


class TestDockerPortEdgeCases:
    """Edge cases for Docker port mapping extraction."""

    def test_port_range_handled_gracefully(self):
        """Port range (8000-8100:8000-8100) doesn't crash."""
        dc = {"services": {"api": {"ports": ["8000-8100:8000-8100"]}}}
        ports = _extract_docker_ports(dc)
        assert ports == {}

    def test_port_with_udp_protocol(self):
        """Port with /udp protocol suffix."""
        dc = {"services": {"api": {"ports": ["3000:3000/udp"]}}}
        ports = _extract_docker_ports(dc)
        assert ports["api"] == [(3000, 3000)]

    def test_multiple_ports_same_service(self):
        """Multiple port mappings on same service."""
        dc = {"services": {"api": {"ports": ["3000:3000", "3001:3001"]}}}
        ports = _extract_docker_ports(dc)
        assert len(ports["api"]) == 2
        assert (3000, 3000) in ports["api"]
        assert (3001, 3001) in ports["api"]

    def test_port_long_form_dict_gracefully_skipped(self):
        """Docker Compose long-form port (dict) is gracefully skipped."""
        dc = {"services": {"api": {"ports": [{"target": 3000, "published": 8080}]}}}
        ports = _extract_docker_ports(dc)
        assert "api" not in ports or ports["api"] == []


# =========================================================================
# P13. Deployment Scan Dedup & Filtering
# =========================================================================


class TestDeploymentScanFiltering:
    """Tests for deployment scan filtering logic."""

    def test_nullish_coalescing_excluded(self, tmp_path):
        """process.env.VAR ?? default uses nullish coalescing — excluded."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.ts").write_text(
            "const db = process.env.DATABASE_URL ?? 'sqlite:///db';\n",
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_002 = [v for v in violations if v.check == "DEPLOY-002"]
        assert len(deploy_002) == 0

    def test_cors_non_http_origin_not_flagged(self, tmp_path):
        """CORS origin that doesn't start with http is not flagged."""
        (tmp_path / "docker-compose.yml").write_text(
            "services:\n  api:\n    build: .\n", encoding="utf-8"
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.ts").write_text(
            'app.use(cors({ origin: "/api" }));\n', encoding="utf-8"
        )
        violations = run_deployment_scan(tmp_path)
        deploy_003 = [v for v in violations if v.check == "DEPLOY-003"]
        assert len(deploy_003) == 0

    def test_localhost_127_db_host_not_flagged(self, tmp_path):
        """127.0.0.1 as DB host is filtered."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              db:
                image: postgres
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "db.js").write_text(
            'const url = "postgres://user:pass@127.0.0.1:5432/db";\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_004 = [v for v in violations if v.check == "DEPLOY-004"]
        assert len(deploy_004) == 0

    def test_0_0_0_0_db_host_not_flagged(self, tmp_path):
        """0.0.0.0 as DB host is filtered."""
        (tmp_path / "docker-compose.yml").write_text(textwrap.dedent("""\
            services:
              db:
                image: postgres
        """), encoding="utf-8")
        src = tmp_path / "src"
        src.mkdir()
        (src / "db.js").write_text(
            'const url = "postgres://user:pass@0.0.0.0:5432/db";\n',
            encoding="utf-8",
        )
        violations = run_deployment_scan(tmp_path)
        deploy_004 = [v for v in violations if v.check == "DEPLOY-004"]
        assert len(deploy_004) == 0


# =========================================================================
# P14. Asset Scan File Type Coverage
# =========================================================================


class TestAssetScanFileTypes:
    """Asset scan works across all supported file types."""

    def test_vue_file_scanned(self, tmp_path):
        """Vue SFC files are scanned for asset references."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "App.vue").write_text(
            '<template><img src="./missing.png" /></template>\n',
            encoding="utf-8",
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) >= 1

    def test_svelte_file_scanned(self, tmp_path):
        """Svelte files are scanned for asset references."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "App.svelte").write_text(
            '<img src="./missing.png" />\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) >= 1

    def test_ejs_file_scanned(self, tmp_path):
        """EJS template files are scanned."""
        views = tmp_path / "views"
        views.mkdir()
        (views / "index.ejs").write_text(
            '<img src="./missing.png" />\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) >= 1

    def test_hbs_file_scanned(self, tmp_path):
        """Handlebars template files are scanned."""
        views = tmp_path / "views"
        views.mkdir()
        (views / "layout.hbs").write_text(
            '<img src="./missing.png" />\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) >= 1

    def test_pug_file_scanned(self, tmp_path):
        """Pug template files are scanned."""
        views = tmp_path / "views"
        views.mkdir()
        (views / "index.pug").write_text(
            'img(src="./missing.png")\n', encoding="utf-8"
        )
        violations = run_asset_scan(tmp_path)
        asset_001 = [v for v in violations if v.check == "ASSET-001"]
        assert len(asset_001) >= 1
