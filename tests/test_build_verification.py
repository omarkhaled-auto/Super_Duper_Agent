"""Tests for build verification (Agent 7) and verification helpers."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from agent_team.verification import _detect_build_command, _check_test_quality, _run_security_checks


class TestDetectBuildCommand:
    def test_npm_build_script(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"scripts": {"build": "next build"}}), encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result == ["npm", "run", "build"]

    def test_npm_tsc_script(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"scripts": {"tsc": "tsc"}}), encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result == ["npm", "run", "tsc"]

    def test_no_build_script(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"scripts": {"test": "jest"}}), encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result is None

    def test_python_pyproject_build(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[build-system]\nrequires = [\"setuptools\"]\n", encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result is not None
        assert "build" in result

    def test_empty_project(self, tmp_path):
        result = _detect_build_command(tmp_path)
        assert result is None

    def test_tsconfig_alone_not_build(self, tmp_path):
        """tsconfig.json alone should NOT trigger build (type check handles it)."""
        tsconfig = tmp_path / "tsconfig.json"
        tsconfig.write_text('{"compilerOptions": {}}', encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result is None

    def test_malformed_package_json(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text("not json{{{", encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result is None

    def test_build_script_priority_over_tsc(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"scripts": {"build": "next build", "tsc": "tsc"}}), encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result == ["npm", "run", "build"]


    def test_package_json_is_array(self, tmp_path):
        """package.json that is a JSON array (not dict) should not crash."""
        pkg = tmp_path / "package.json"
        pkg.write_text('[1, 2, 3]', encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result is None

    def test_package_json_scripts_null(self, tmp_path):
        """package.json with "scripts": null should not crash."""
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"scripts": None}), encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result is None

    def test_package_json_scripts_string(self, tmp_path):
        """package.json with "scripts": "invalid" should not crash."""
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"scripts": "not a dict"}), encoding="utf-8")
        result = _detect_build_command(tmp_path)
        assert result is None


class TestBuildPhaseExceptionHandling:
    """Tests for Phase 1.5 try/except wrapping (Fix 3)."""

    @pytest.mark.asyncio
    async def test_build_detect_exception_does_not_crash_pipeline(self, tmp_path, monkeypatch):
        """If _detect_build_command raises, the pipeline should continue."""
        from agent_team.verification import verify_task_completion
        from agent_team.contracts import ContractRegistry

        def raise_error(root):
            raise RuntimeError("Simulated build detection failure")

        monkeypatch.setattr("agent_team.verification._detect_build_command", raise_error)

        registry = ContractRegistry()
        result = await verify_task_completion(
            "T-BUILD-ERR", tmp_path, registry,
            run_build=True, run_lint=False, run_type_check=False, run_tests=False,
        )
        # Pipeline should not crash; build_passed stays None (not run)
        assert result.task_id == "T-BUILD-ERR"
        assert any("Build check failed" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_build_phase_skipped_when_disabled(self, tmp_path):
        """When run_build=False, build phase should be skipped entirely."""
        from agent_team.verification import verify_task_completion
        from agent_team.contracts import ContractRegistry

        registry = ContractRegistry()
        result = await verify_task_completion(
            "T-NO-BUILD", tmp_path, registry,
            run_build=False, run_lint=False, run_type_check=False, run_tests=False,
        )
        assert result.build_passed is None


class TestCheckTestQuality:
    """Tests for _check_test_quality (Root Cause #6)."""

    def test_no_test_files_returns_none(self, tmp_path):
        result = _check_test_quality(tmp_path)
        assert result is None

    def test_python_tests_with_assertions(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_example.py"
        test_file.write_text(
            "def test_one():\n    assert 1 == 1\n\n"
            "def test_two():\n    assert True\n",
            encoding="utf-8",
        )
        result = _check_test_quality(tmp_path)
        assert result is not None
        assert result["total"] == 2
        assert result["empty"] == 0
        assert result["score"] == 1.0

    def test_python_empty_tests_detected(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_example.py"
        test_file.write_text(
            "def test_empty():\n    pass\n",
            encoding="utf-8",
        )
        result = _check_test_quality(tmp_path)
        assert result is not None
        assert result["total"] == 1
        assert result["empty"] == 1
        assert result["score"] == 0.0
        assert any("no assertions" in i for i in result["issues"])

    def test_skipped_tests_detected(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_example.py"
        test_file.write_text(
            "@pytest.mark.skip\ndef test_skipped():\n    assert True\n",
            encoding="utf-8",
        )
        result = _check_test_quality(tmp_path)
        assert result is not None
        assert result["skipped"] >= 1
        assert any("skipped" in i for i in result["issues"])

    def test_minimum_count_enforcement(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_example.py"
        test_file.write_text(
            "def test_one():\n    assert True\n",
            encoding="utf-8",
        )
        result = _check_test_quality(tmp_path, min_test_count=10)
        assert result is not None
        assert any("minimum required" in i for i in result["issues"])

    def test_js_tests_with_expect(self, tmp_path):
        tests_dir = tmp_path / "__tests__"
        tests_dir.mkdir()
        test_file = tests_dir / "app.test.ts"
        test_file.write_text(
            'it("works", () => { expect(1).toBe(1); });\n'
            'test("also works", () => { expect(true).toBeTruthy(); });\n',
            encoding="utf-8",
        )
        result = _check_test_quality(tmp_path)
        assert result is not None
        assert result["total"] == 2
        assert result["empty"] == 0


class TestRunSecurityChecks:
    """Tests for _run_security_checks (Root Cause #5)."""

    @pytest.mark.asyncio
    async def test_empty_project(self, tmp_path):
        issues = await _run_security_checks(tmp_path)
        assert issues == []

    @pytest.mark.asyncio
    async def test_detects_env_without_gitignore(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=abc123", encoding="utf-8")
        issues = await _run_security_checks(tmp_path)
        assert any(".env" in i for i in issues)

    @pytest.mark.asyncio
    async def test_env_ok_when_gitignored(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=abc123", encoding="utf-8")
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".env\nnode_modules/\n", encoding="utf-8")
        issues = await _run_security_checks(tmp_path)
        assert not any(".env" in i and "not in .gitignore" in i for i in issues)

    @pytest.mark.asyncio
    async def test_detects_hardcoded_api_key(self, tmp_path):
        src = tmp_path / "config.ts"
        src.write_text(
            'const api_key = "sk_live_' + 'X' * 32 + '";\n',
            encoding="utf-8",
        )
        issues = await _run_security_checks(tmp_path)
        assert any("Stripe/OpenAI" in i or "API key" in i for i in issues)

    @pytest.mark.asyncio
    async def test_detects_github_pat(self, tmp_path):
        src = tmp_path / "deploy.py"
        src.write_text(
            'TOKEN = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"\n',
            encoding="utf-8",
        )
        issues = await _run_security_checks(tmp_path)
        assert any("GitHub" in i for i in issues)

    @pytest.mark.asyncio
    async def test_no_false_positive_on_clean_code(self, tmp_path):
        src = tmp_path / "app.ts"
        src.write_text(
            'const apiKey = process.env.API_KEY;\n'
            'console.log("Hello world");\n',
            encoding="utf-8",
        )
        issues = await _run_security_checks(tmp_path)
        assert not any("hardcoded" in i.lower() or "API key" in i for i in issues)
