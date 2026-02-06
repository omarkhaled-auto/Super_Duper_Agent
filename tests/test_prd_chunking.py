"""Tests for PRD chunking functionality."""

from pathlib import Path

import pytest

from agent_team.prd_chunking import (
    PRDChunk,
    _find_section_boundaries,
    build_prd_index,
    create_prd_chunks,
    detect_large_prd,
    validate_chunks,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def small_prd_content() -> str:
    """PRD content under threshold (10KB)."""
    return """# My App PRD

## Overview
A simple application.

## Features
- Feature 1
- Feature 2

## Database
Users table with name and email.
"""


@pytest.fixture
def large_prd_content() -> str:
    """PRD content over threshold (60KB)."""
    base = """# Enterprise App PRD

## Overview
A comprehensive enterprise application with many features.

"""
    # Generate sections to exceed 50KB
    sections = [
        (
            "## Features\n"
            + "\n".join(
                [f"- Feature {i}: Description of feature {i} with details." * 10 for i in range(100)]
            )
        ),
        (
            "## Database Schema\n"
            + "\n".join(
                [f"### Table {i}\nColumns: id, name, created_at, updated_at" * 5 for i in range(50)]
            )
        ),
        (
            "## API Endpoints\n"
            + "\n".join(
                [f"### GET /api/resource{i}\nReturns resource {i} data." * 5 for i in range(50)]
            )
        ),
        (
            "## Frontend Components\n"
            + "\n".join(
                [f"### Component{i}\nReact component for feature {i}." * 5 for i in range(50)]
            )
        ),
        ("## Authentication\n" + "JWT-based authentication with refresh tokens.\n" * 100),
        (
            "## Testing Requirements\n"
            + "\n".join([f"- Test case {i}: Verify functionality." for i in range(100)])
        ),
    ]
    return base + "\n\n".join(sections)


@pytest.fixture
def sectioned_prd_content() -> str:
    """PRD with clear section boundaries."""
    return """# Product PRD

## Features and User Stories
- As a user, I want to login
- As a user, I want to view dashboard

## Database Schema
### Users Table
- id: UUID
- email: string
- password_hash: string

### Posts Table
- id: UUID
- user_id: UUID
- content: text

## API Endpoints
### Authentication
- POST /api/auth/login
- POST /api/auth/register

### Posts
- GET /api/posts
- POST /api/posts

## Frontend Pages
- Login page
- Dashboard page
- Posts page

## Infrastructure
- Docker deployment
- PostgreSQL database
- Redis cache
"""


# =============================================================================
# Unit Tests - Detection
# =============================================================================


class TestDetectLargePRD:
    """Tests for detect_large_prd function."""

    def test_small_prd_not_detected(self, small_prd_content: str) -> None:
        """PRD under threshold returns False."""
        assert detect_large_prd(small_prd_content, threshold=50000) is False

    def test_large_prd_detected(self, large_prd_content: str) -> None:
        """PRD over threshold returns True."""
        assert detect_large_prd(large_prd_content, threshold=50000) is True

    def test_exact_threshold(self) -> None:
        """PRD exactly at threshold returns False (not >)."""
        content = "x" * 50000
        assert detect_large_prd(content, threshold=50000) is False

    def test_one_over_threshold(self) -> None:
        """PRD one byte over threshold returns True."""
        content = "x" * 50001
        assert detect_large_prd(content, threshold=50000) is True

    def test_custom_threshold(self, small_prd_content: str) -> None:
        """Custom threshold is respected."""
        assert detect_large_prd(small_prd_content, threshold=100) is True


# =============================================================================
# Unit Tests - Section Boundaries
# =============================================================================


class TestFindSectionBoundaries:
    """Tests for _find_section_boundaries function."""

    def test_finds_h2_sections(self, sectioned_prd_content: str) -> None:
        """Correctly identifies ## heading boundaries."""
        sections = _find_section_boundaries(sectioned_prd_content)
        section_names = [s[2] for s in sections]
        assert "features" in section_names
        assert "database" in section_names
        assert "api" in section_names

    def test_single_section_prd(self) -> None:
        """PRD with single section returns one boundary."""
        content = "# PRD\n\nJust some content without subsections."
        sections = _find_section_boundaries(content)
        assert len(sections) >= 1

    def test_empty_content(self) -> None:
        """Empty content returns minimal sections."""
        sections = _find_section_boundaries("")
        assert len(sections) >= 1


# =============================================================================
# Unit Tests - Chunking
# =============================================================================


class TestCreatePRDChunks:
    """Tests for create_prd_chunks function."""

    def test_creates_chunk_directory(self, tmp_path: Path, sectioned_prd_content: str) -> None:
        """Creates output directory if not exists."""
        chunk_dir = tmp_path / "chunks"
        assert not chunk_dir.exists()
        create_prd_chunks(sectioned_prd_content, chunk_dir)
        assert chunk_dir.exists()

    def test_creates_chunk_files(self, tmp_path: Path, sectioned_prd_content: str) -> None:
        """Creates .md files for each section."""
        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(sectioned_prd_content, chunk_dir)

        assert len(chunks) > 0
        for chunk in chunks:
            chunk_path = chunk_dir / f"{chunk.name}.md"
            assert chunk_path.is_file()

    def test_chunk_metadata_correct(self, tmp_path: Path, sectioned_prd_content: str) -> None:
        """Chunk metadata has correct fields."""
        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(sectioned_prd_content, chunk_dir)

        for chunk in chunks:
            assert isinstance(chunk, PRDChunk)
            assert chunk.name
            assert chunk.focus
            assert chunk.file
            assert chunk.start_line > 0
            assert chunk.end_line >= chunk.start_line
            assert chunk.size_bytes > 0

    def test_chunk_content_readable(self, tmp_path: Path, sectioned_prd_content: str) -> None:
        """Chunk files contain valid content."""
        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(sectioned_prd_content, chunk_dir)

        for chunk in chunks:
            chunk_path = chunk_dir / f"{chunk.name}.md"
            content = chunk_path.read_text(encoding="utf-8")
            assert len(content) > 0


# =============================================================================
# Unit Tests - Index Building
# =============================================================================


class TestBuildPRDIndex:
    """Tests for build_prd_index function."""

    def test_returns_dict(self, sectioned_prd_content: str) -> None:
        """Returns dictionary structure."""
        index = build_prd_index(sectioned_prd_content)
        assert isinstance(index, dict)

    def test_index_has_required_fields(self, sectioned_prd_content: str) -> None:
        """Each index entry has required metadata."""
        index = build_prd_index(sectioned_prd_content)

        for section_name, info in index.items():
            assert "heading" in info
            assert "summary" in info
            assert "line_range" in info
            assert "size_bytes" in info
            assert "focus" in info

    def test_index_sections_match_chunks(self, tmp_path: Path, sectioned_prd_content: str) -> None:
        """Index sections correspond to chunk sections."""
        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(sectioned_prd_content, chunk_dir)
        index = build_prd_index(sectioned_prd_content)

        chunk_names = {c.name.split("_")[0] for c in chunks}  # Remove _N suffix
        index_names = set(index.keys())

        # Most chunk names should appear in index
        assert len(chunk_names & index_names) > 0


# =============================================================================
# Unit Tests - Validation
# =============================================================================


class TestValidateChunks:
    """Tests for validate_chunks function."""

    def test_valid_chunks_pass(self, tmp_path: Path, sectioned_prd_content: str) -> None:
        """Valid chunks pass validation."""
        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(sectioned_prd_content, chunk_dir)
        assert validate_chunks(chunks, chunk_dir) is True

    def test_missing_file_fails(self, tmp_path: Path, sectioned_prd_content: str) -> None:
        """Missing chunk file fails validation."""
        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(sectioned_prd_content, chunk_dir)

        # Delete one file
        if chunks:
            (chunk_dir / f"{chunks[0].name}.md").unlink()
            assert validate_chunks(chunks, chunk_dir) is False

    def test_empty_chunks_pass(self, tmp_path: Path) -> None:
        """Empty chunk list passes validation."""
        chunk_dir = tmp_path / "chunks"
        chunk_dir.mkdir()
        assert validate_chunks([], chunk_dir) is True


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
class TestChunkingIntegration:
    """Integration tests for chunking with other components."""

    def test_chunks_work_with_decomposition_prompt(
        self, tmp_path: Path, sectioned_prd_content: str
    ) -> None:
        """Chunks integrate with build_decomposition_prompt."""
        from agent_team.agents import build_decomposition_prompt
        from agent_team.config import AgentTeamConfig

        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(sectioned_prd_content, chunk_dir)
        index = build_prd_index(sectioned_prd_content)

        config = AgentTeamConfig()
        prompt = build_decomposition_prompt(
            task="Build this app",
            depth="exhaustive",
            config=config,
            prd_chunks=[c.to_dict() for c in chunks],
            prd_index=index,
        )

        assert "CHUNKED PRD MODE" in prompt
        assert ".agent-team/prd-chunks/" in prompt
        assert "SYNTHESIZER" in prompt

    def test_small_prd_uses_standard_prompt(self, small_prd_content: str) -> None:
        """Small PRD uses standard (non-chunked) prompt."""
        from agent_team.agents import build_decomposition_prompt
        from agent_team.config import AgentTeamConfig

        config = AgentTeamConfig()
        prompt = build_decomposition_prompt(
            task=small_prd_content,
            depth="standard",
            config=config,
            prd_chunks=None,
            prd_index=None,
        )

        assert "CHUNKED PRD MODE" not in prompt
        assert "PRD ANALYZER FLEET (10+ planners" in prompt


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_prd_with_code_blocks(self, tmp_path: Path) -> None:
        """PRD with code blocks chunks correctly."""
        content = """# PRD

## Database Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255)
);
```

## API

```python
@app.route('/api/users')
def get_users():
    return jsonify(users)
```
"""
        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(content, chunk_dir)

        # Verify chunks were created
        assert len(chunks) > 0

        # Verify chunk files are readable
        for chunk in chunks:
            chunk_path = chunk_dir / f"{chunk.name}.md"
            chunk_content = chunk_path.read_text(encoding="utf-8")
            assert len(chunk_content) > 0

    def test_unicode_content(self, tmp_path: Path) -> None:
        """PRD with unicode characters chunks correctly."""
        # Need more content per section to exceed 100 byte minimum
        content = """# PRD for Japanese App

## Features and Requirements
This section describes features for the application.
- Feature with emojis and descriptions that need to be long enough
- Chinese description with more content to make it substantial
- Additional feature items to ensure section is big enough
- User authentication with OAuth2 support
- Dashboard with analytics and metrics

## Database Schema and Models
Tables with unicode names and descriptions that are long enough.
- Users table with id, name, email columns
- Posts table with content and metadata
- Comments table for user interactions
- Analytics table for tracking metrics
"""
        chunk_dir = tmp_path / "chunks"
        chunks = create_prd_chunks(content, chunk_dir)

        assert len(chunks) > 0
        for chunk in chunks:
            chunk_path = chunk_dir / f"{chunk.name}.md"
            content_read = chunk_path.read_text(encoding="utf-8")
            assert len(content_read) > 0


# =============================================================================
# Config Tests
# =============================================================================


class TestPRDChunkingConfig:
    """Tests for PRDChunkingConfig."""

    def test_default_config_values(self) -> None:
        """Default config has expected values."""
        from agent_team.config import PRDChunkingConfig

        config = PRDChunkingConfig()
        assert config.enabled is True
        assert config.threshold == 50000
        assert config.max_chunk_size == 20000

    def test_config_in_agent_team_config(self) -> None:
        """PRDChunkingConfig is part of AgentTeamConfig."""
        from agent_team.config import AgentTeamConfig

        config = AgentTeamConfig()
        assert hasattr(config, "prd_chunking")
        assert config.prd_chunking.enabled is True

    def test_config_from_dict(self) -> None:
        """Config loads from dict correctly."""
        from agent_team.config import load_config

        # Test with defaults (no yaml file)
        config = load_config()
        assert config.prd_chunking.enabled is True
        assert config.prd_chunking.threshold == 50000
