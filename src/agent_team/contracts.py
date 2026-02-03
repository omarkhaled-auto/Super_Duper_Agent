"""Contract registry with JSON persistence and deterministic verification.

Defines module and wiring contracts that specify which symbols a module must
export and how modules are wired together via imports.  Contracts are persisted
as JSON (``CONTRACTS.json``) and can be verified against the actual source tree
to detect drift between the declared architecture and the implementation.

All file paths stored inside contracts use POSIX-normalized format regardless
of the host operating system.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._lang import detect_language as _detect_language  # Finding #11: shared module


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ExportedSymbol:
    """A single symbol exported by a module."""

    name: str
    kind: str  # "function" | "class" | "interface" | "type" | "const"
    signature: str | None = None  # e.g. "(user_id: str) -> UserProfile"


@dataclass
class ModuleContract:
    """Declares which symbols a module must export."""

    module_path: str  # POSIX-normalized
    exports: list[ExportedSymbol] = field(default_factory=list)
    created_by_task: str = ""  # task ID that created this contract


@dataclass
class WiringContract:
    """Declares that *source_module* imports specific symbols from *target_module*."""

    source_module: str
    target_module: str
    imports: list[str]  # symbol names
    created_by_task: str = ""


@dataclass
class ContractRegistry:
    """Top-level container for all module and wiring contracts."""

    modules: dict[str, ModuleContract] = field(default_factory=dict)  # path -> contract
    wirings: list[WiringContract] = field(default_factory=list)
    file_missing: bool = False  # True when no CONTRACTS.json was found on disk


@dataclass
class ContractViolation:
    """Describes a single contract violation found during verification."""

    contract_type: str  # "module" | "wiring"
    description: str
    file_path: str
    expected: str
    actual: str
    severity: str  # "error" | "warning"


@dataclass
class VerificationResult:
    """Aggregate result of verifying all contracts in a registry."""

    passed: bool
    violations: list[ContractViolation] = field(default_factory=list)
    checked_modules: int = 0
    checked_wirings: int = 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_file_safe(path: Path) -> str | None:
    """Read *path* with ``utf-8-sig`` encoding, return ``None`` on any error."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError, PermissionError):
        return None


# ---------------------------------------------------------------------------
# Symbol presence checks
# ---------------------------------------------------------------------------

def _symbol_present_py(file_content: str, symbol: ExportedSymbol) -> bool:
    """Check whether a Python file exports *symbol*.

    Strategy:
    1. Parse with :func:`ast.parse`.
    2. If ``__all__`` is defined at module level, *symbol.name* must appear
       in that list (authoritative).
    3. Otherwise fall back to scanning ``tree.body`` for matching
       definitions (``def``, ``class``, assignments).
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return False

    # ------------------------------------------------------------------
    # 1. Check __all__ first (authoritative when present)
    # ------------------------------------------------------------------
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        names: list[str] = []
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(
                                elt.value, str
                            ):
                                names.append(elt.value)
                        return symbol.name in names

    # ------------------------------------------------------------------
    # 2. Fall back to tree.body scan
    # ------------------------------------------------------------------
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == symbol.name:
                return True
        elif isinstance(node, ast.ClassDef):
            if node.name == symbol.name:
                return True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol.name:
                    return True
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == symbol.name:
                return True

    return False


def _symbol_present_ts(file_content: str, symbol: ExportedSymbol) -> bool:
    """Check whether a TypeScript/JavaScript file exports *symbol*.

    Uses regex patterns to detect various export forms:

    * ``export function NAME``
    * ``export class NAME``
    * ``export const NAME``
    * ``export default NAME``
    * ``export type NAME``
    * ``export interface NAME``
    * ``export enum NAME``
    * ``export { NAME }`` or ``export { NAME as ... }``
    """
    name = re.escape(symbol.name)
    patterns = [
        rf"export\s+(?:async\s+)?function\s+{name}\b",
        rf"export\s+class\s+{name}\b",
        rf"export\s+(?:const|let|var)\s+{name}\b",
        rf"export\s+default\s+(?:class|function)?\s*{name}\b",
        rf"export\s+type\s+{name}\b",
        rf"export\s+interface\s+{name}\b",
        rf"export\s+enum\s+{name}\b",
        rf"export\s*\{{[^}}]*\b{name}\b[^}}]*\}}",  # export { Name, ... }
    ]
    return any(re.search(p, file_content) for p in patterns)


# ---------------------------------------------------------------------------
# JSON serialization / deserialization
# ---------------------------------------------------------------------------

def _registry_to_dict(registry: ContractRegistry) -> dict[str, Any]:
    """Convert *registry* to a JSON-serializable :class:`dict`."""
    return {
        "version": "1.0",
        "modules": {
            path: {
                "exports": [
                    {
                        "name": s.name,
                        "kind": s.kind,
                        "signature": s.signature,
                    }
                    for s in contract.exports
                ],
                "created_by_task": contract.created_by_task,
            }
            for path, contract in registry.modules.items()
        },
        "wirings": [
            {
                "source_module": w.source_module,
                "target_module": w.target_module,
                "imports": w.imports,
                "created_by_task": w.created_by_task,
            }
            for w in registry.wirings
        ],
    }


def _dict_to_registry(data: dict[str, Any]) -> ContractRegistry:
    """Convert a JSON :class:`dict` back to a :class:`ContractRegistry`."""
    registry = ContractRegistry()

    for path, mod_data in data.get("modules", {}).items():
        exports = [
            ExportedSymbol(
                name=e["name"],
                kind=e["kind"],
                signature=e.get("signature"),
            )
            for e in mod_data.get("exports", [])
        ]
        registry.modules[path] = ModuleContract(
            module_path=path,
            exports=exports,
            created_by_task=mod_data.get("created_by_task", ""),
        )

    for w_data in data.get("wirings", []):
        registry.wirings.append(
            WiringContract(
                source_module=w_data["source_module"],
                target_module=w_data["target_module"],
                imports=w_data.get("imports", []),
                created_by_task=w_data.get("created_by_task", ""),
            )
        )

    return registry


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_contracts(path: Path) -> ContractRegistry:
    """Load a :class:`ContractRegistry` from a JSON file.

    If the file does not exist an empty registry is returned.  A
    :exc:`json.JSONDecodeError` is allowed to propagate so callers are
    made aware of malformed contract files.

    Expected JSON schema::

        {
            "version": "1.0",
            "modules": {
                "src/services/auth.py": {
                    "exports": [
                        {"name": "AuthService", "kind": "class", "signature": null}
                    ],
                    "created_by_task": "TASK-005"
                }
            },
            "wirings": [
                {
                    "source_module": "src/routes/auth.py",
                    "target_module": "src/services/auth.py",
                    "imports": ["AuthService"],
                    "created_by_task": "TASK-005"
                }
            ]
        }
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        registry = ContractRegistry()
        registry.file_missing = True
        return registry

    data = json.loads(raw)  # JSONDecodeError propagates intentionally
    return _dict_to_registry(data)


def save_contracts(registry: ContractRegistry, path: Path) -> None:
    """Save *registry* to a JSON file.

    Parent directories are created automatically.  The output includes a
    top-level ``"version": "1.0"`` field for forward-compatibility.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _registry_to_dict(registry)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_module_contract(
    contract: ModuleContract,
    project_root: Path,
) -> list[ContractViolation]:
    """Verify that a module exports the symbols declared in *contract*.

    Steps:

    1. Resolve the file at ``project_root / contract.module_path``.
    2. Detect the language from the file extension.
    3. For Python files use :func:`_symbol_present_py`.
    4. For TypeScript / JavaScript files use :func:`_symbol_present_ts`.
    5. Return a :class:`ContractViolation` for each missing symbol.
    """
    violations: list[ContractViolation] = []
    file_path = project_root / contract.module_path
    content = _read_file_safe(file_path)

    if content is None:
        violations.append(
            ContractViolation(
                contract_type="module",
                description=f"Module file not found: {contract.module_path}",
                file_path=contract.module_path,
                expected="file exists",
                actual="file not found",
                severity="error",
            )
        )
        return violations

    language = _detect_language(contract.module_path)

    for symbol in contract.exports:
        present = False
        if language == "python":
            present = _symbol_present_py(content, symbol)
        elif language in ("typescript", "javascript"):
            present = _symbol_present_ts(content, symbol)
        else:
            # Unknown language — cannot verify; emit a warning.
            violations.append(
                ContractViolation(
                    contract_type="module",
                    description=(
                        f"Cannot verify symbol '{symbol.name}' — "
                        f"unsupported language for {contract.module_path}"
                    ),
                    file_path=contract.module_path,
                    expected=f"export {symbol.kind} {symbol.name}",
                    actual="unknown language",
                    severity="warning",
                )
            )
            continue

        if not present:
            violations.append(
                ContractViolation(
                    contract_type="module",
                    description=(
                        f"Symbol '{symbol.name}' ({symbol.kind}) not found "
                        f"in {contract.module_path}"
                    ),
                    file_path=contract.module_path,
                    expected=f"export {symbol.kind} {symbol.name}",
                    actual="symbol not found",
                    severity="error",
                )
            )

    return violations


def verify_wiring_contract(
    contract: WiringContract,
    project_root: Path,
) -> list[ContractViolation]:
    """Verify a wiring contract.

    Checks:

    1. The *target_module* exports every symbol listed in ``contract.imports``.
    2. The *source_module* contains an import statement for each symbol.

    Returns a :class:`ContractViolation` for every missing export or import.
    """
    violations: list[ContractViolation] = []

    # ------------------------------------------------------------------
    # Read both files
    # ------------------------------------------------------------------
    target_path = project_root / contract.target_module
    source_path = project_root / contract.source_module

    target_content = _read_file_safe(target_path)
    source_content = _read_file_safe(source_path)

    if target_content is None:
        violations.append(
            ContractViolation(
                contract_type="wiring",
                description=f"Target module not found: {contract.target_module}",
                file_path=contract.target_module,
                expected="file exists",
                actual="file not found",
                severity="error",
            )
        )

    if source_content is None:
        violations.append(
            ContractViolation(
                contract_type="wiring",
                description=f"Source module not found: {contract.source_module}",
                file_path=contract.source_module,
                expected="file exists",
                actual="file not found",
                severity="error",
            )
        )

    # If either file is missing we cannot perform further checks.
    if target_content is None or source_content is None:
        return violations

    target_lang = _detect_language(contract.target_module)
    source_lang = _detect_language(contract.source_module)

    for symbol_name in contract.imports:
        sym = ExportedSymbol(name=symbol_name, kind="unknown")

        # -- Check target exports the symbol --------------------------------
        target_exported = False
        if target_lang == "python":
            target_exported = _symbol_present_py(target_content, sym)
        elif target_lang in ("typescript", "javascript"):
            target_exported = _symbol_present_ts(target_content, sym)

        if not target_exported:
            violations.append(
                ContractViolation(
                    contract_type="wiring",
                    description=(
                        f"Target module '{contract.target_module}' does not "
                        f"export '{symbol_name}'"
                    ),
                    file_path=contract.target_module,
                    expected=f"exports {symbol_name}",
                    actual="symbol not exported",
                    severity="error",
                )
            )

        # -- Check source imports the symbol --------------------------------
        escaped = re.escape(symbol_name)
        source_imports = False

        if source_lang == "python":
            # Covers: from ... import symbol_name  /  import ... symbol_name
            source_imports = bool(
                re.search(rf"\bimport\b.*\b{escaped}\b", source_content)
            )
        elif source_lang in ("typescript", "javascript"):
            # Covers: import { symbol_name } ...  /  import symbol_name ...
            source_imports = bool(
                re.search(rf"\bimport\b.*\b{escaped}\b", source_content)
            )

        if not source_imports:
            violations.append(
                ContractViolation(
                    contract_type="wiring",
                    description=(
                        f"Source module '{contract.source_module}' does not "
                        f"import '{symbol_name}' from '{contract.target_module}'"
                    ),
                    file_path=contract.source_module,
                    expected=f"imports {symbol_name}",
                    actual="import not found",
                    severity="error",
                )
            )

    return violations


def verify_all_contracts(
    registry: ContractRegistry,
    project_root: Path,
) -> VerificationResult:
    """Verify every module and wiring contract in *registry*.

    Returns a :class:`VerificationResult` summarising all violations found.
    """
    all_violations: list[ContractViolation] = []
    checked_modules = 0
    checked_wirings = 0

    for contract in registry.modules.values():
        all_violations.extend(verify_module_contract(contract, project_root))
        checked_modules += 1

    for wiring in registry.wirings:
        all_violations.extend(verify_wiring_contract(wiring, project_root))
        checked_wirings += 1

    return VerificationResult(
        passed=len(all_violations) == 0,
        violations=all_violations,
        checked_modules=checked_modules,
        checked_wirings=checked_wirings,
    )
