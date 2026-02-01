"""Enumerated constants for Agent Team.

Using ``str, Enum`` so values serialize naturally as plain strings
in YAML/JSON while still providing type safety and IDE autocompletion.
"""

from __future__ import annotations

from enum import Enum


class DepthLevel(str, Enum):
    """Task analysis depth levels."""
    QUICK = "quick"
    STANDARD = "standard"
    THOROUGH = "thorough"
    EXHAUSTIVE = "exhaustive"


class TaskStatus(str, Enum):
    """Scheduler task statuses."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class VerificationStatus(str, Enum):
    """Result of a verification check."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


class HealthStatus(str, Enum):
    """Overall project health."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class Severity(str, Enum):
    """Contract violation severity."""
    ERROR = "error"
    WARNING = "warning"


class ConflictStrategy(str, Enum):
    """Scheduler conflict resolution strategies."""
    ARTIFICIAL_DEPENDENCY = "artificial-dependency"
    INTEGRATION_AGENT = "integration-agent"


class DesignReferenceDepth(str, Enum):
    """Design reference scraping depth."""
    BRANDING = "branding"
    SCREENSHOTS = "screenshots"
    FULL = "full"


class ReviewPhase(str, Enum):
    """Verification review phases."""
    CONTRACTS = "contracts"
    LINT = "lint"
    TYPE_CHECK = "type_check"
    TESTS = "tests"
