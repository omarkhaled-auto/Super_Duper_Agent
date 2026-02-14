# AUDIT: Tree-Sitter + Code Analysis Patterns in Build 1 PRD

**Auditor:** Tree-Sitter Technical Reviewer
**Date:** 2026-02-14
**Scope:** BUILD1_PRD.md — Codebase Intelligence module (Milestones 5-6)
**Research:** Context7 (py-tree-sitter docs), PyPI package metadata, GitHub source bindings, py-tree-sitter v0.25.2 documentation

---

## Executive Summary

The Build 1 PRD's tree-sitter usage is **technically accurate** for py-tree-sitter v0.25.x. The API patterns (Parser, Language, Query, QueryCursor) match the current stable API. Version pinning is correct. Language grammar packages are properly identified. **No critical issues found.** Two medium-priority clarifications and several informational notes are documented below.

**Verdict: PASS** -- 0 CRITICAL, 0 HIGH, 2 MEDIUM, 3 LOW, 4 INFO

---

## 1. Package Names and Installation

### 1.1 Core Package

| PRD Claim | Actual (PyPI) | Verdict |
|---|---|---|
| `tree-sitter==0.25.2` | Latest: 0.25.2 (Sep 2025) | CORRECT |
| `pip install tree-sitter` | Correct package name | CORRECT |
| `from tree_sitter import Language, Parser` | Confirmed via Context7 + README | CORRECT |

### 1.2 Language Grammar Packages

| PRD Claim | Actual (PyPI) | Import Name | Verdict |
|---|---|---|---|
| `tree-sitter-python==0.25.0` | 0.25.0 available | `tree_sitter_python` | CORRECT |
| `tree-sitter-typescript==0.23.2` | 0.23.2 (Nov 2024) | `tree_sitter_typescript` | CORRECT |
| `tree-sitter-c-sharp==0.23.1` | 0.23.1 (Nov 2024) | `tree_sitter_c_sharp` | CORRECT |
| `tree-sitter-go==0.25.0` | 0.25.0 available | `tree_sitter_go` | CORRECT |

**Evidence (Context7):**
```python
import tree_sitter_python
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)
tree = parser.parse(b"def hello(): pass")
```

---

## 2. API Verification

### 2.1 Parser Class -- CORRECT

**PRD (REQ-042):** "Create Parser(language) and parse file content as bytes"

**Actual v0.25.x API (confirmed via Context7):**
```python
# Option 1: Pass language to constructor
parser = Parser(PY_LANGUAGE)

# Option 2: Set language after creation
parser = Parser()
parser.language = PY_LANGUAGE

# Parse bytes
tree = parser.parse(b"source code here")
tree = parser.parse(bytes(source_code, "utf8"))
```

**Verdict:** CORRECT. Both constructor patterns work. PRD uses the cleaner Option 1.

### 2.2 Language Loading -- CORRECT with clarification needed

**PRD (REQ-042):** "Load appropriate tree-sitter grammar via Language(tree_sitter_xxx.language())"

**Actual binding exports (verified from GitHub source `__init__.py` files):**

| Package | Export | Usage |
|---|---|---|
| `tree_sitter_python` | `language` (callable) | `Language(tree_sitter_python.language())` |
| `tree_sitter_c_sharp` | `language` (callable) | `Language(tree_sitter_c_sharp.language())` |
| `tree_sitter_go` | `language` (callable) | `Language(tree_sitter_go.language())` |
| `tree_sitter_typescript` | `language_typescript` (callable) | `Language(tree_sitter_typescript.language_typescript())` |
| `tree_sitter_typescript` | `language_tsx` (callable) | `Language(tree_sitter_typescript.language_tsx())` |

**ISSUE-1 (MEDIUM):** REQ-042 uses generic `Language(tree_sitter_xxx.language())` but TypeScript does NOT export a `language()` function. It exports `language_typescript()` and `language_tsx()` instead. While TECH-017 correctly documents this, REQ-042 should cross-reference TECH-017 to avoid confusion. An implementor reading only REQ-042 would write incorrect TypeScript loading code.

**Suggested fix for REQ-042:** Add parenthetical: "...via Language(tree_sitter_xxx.language()) (see TECH-017 for TypeScript exception using language_typescript/language_tsx)."

### 2.3 Query + QueryCursor -- CORRECT

**PRD (REQ-043):** "Use `QueryCursor(query)` to execute queries -- `cursor.captures(root_node)` returns `dict[str, list[Node]]` where keys are capture names."

**Actual v0.25.x API (confirmed via Context7 and py-tree-sitter README):**
```python
from tree_sitter import Language, Parser, Query, QueryCursor

query = Query(
    PY_LANGUAGE,
    "(function_definition name: (identifier) @function.def)"
)

query_cursor = QueryCursor(query)
captures = query_cursor.captures(tree.root_node)
# Returns dict[str, list[Node]]
# e.g., {"function.def": [<Node>, <Node>]}
```

**Verdict:** CORRECT. This is the v0.25.x API. The PRD correctly uses `QueryCursor` instead of the deprecated `Query.captures()` / `Query.matches()` that were removed in v0.23.0.

**Historical note:** In py-tree-sitter < 0.23.0, `Query` had `captures()` and `matches()` methods directly. In v0.23.0+ these were removed. In v0.25.0+ they were added to the new `QueryCursor` class. The PRD targets v0.25.2 and correctly uses `QueryCursor`.

### 2.4 Node Properties -- CORRECT

**PRD (TECH-016):** "tree-sitter node.text returns bytes -- always use .decode() for string comparison. start_point is 0-indexed (row, column) -- add 1 for human-readable line numbers"

**Actual (confirmed via Context7):**
```python
function_node = tree.root_node.children[0]

# Text is bytes
assert isinstance(function_node.text, bytes)
name_node.text.decode()  # "foo"

# Points are 0-indexed (row, col)
assert function_node.start_point == (1, 0)  # 0-indexed
line_number = node.start_point[0] + 1       # 1-indexed for display
```

**Verdict:** CORRECT. The `start_point[0] + 1` pattern in REQ-043 is accurate.

### 2.5 TypeScript Dual Language -- CORRECT

**PRD (TECH-017):** "Language(tree_sitter_typescript.language_typescript()) for .ts files and Language(tree_sitter_typescript.language_tsx()) for .tsx files"

**Actual (verified from GitHub `bindings/python/tree_sitter_typescript/__init__.py`):**
The `tree_sitter_typescript` package exports exactly two language bindings:
- `language_typescript` -- for `.ts` files
- `language_tsx` -- for `.tsx` files

There is NO generic `language()` export -- only these two specific functions.

**Verdict:** CORRECT.

### 2.6 Node Navigation -- CORRECT

**PRD (REQ-043, implicit):** Uses `node.text.decode()`, `start_point[0]`, `children`, `child_by_field_name()`

**Actual (confirmed via Context7):**
```python
# Direct children
root_node.children[0]          # list access
root_node.child(0)             # method access

# Named access
function_node.child_by_field_name("name")    # -> identifier node
function_node.child_by_field_name("body")    # -> block node
function_node.child_by_field_name("parameters")  # -> parameters node

# Properties
node.type        # "function_definition"
node.is_named    # True for named nodes
node.start_byte  # byte offset
node.end_byte    # byte offset
node.start_point # (row, col) 0-indexed
node.end_point   # (row, col) 0-indexed
```

**Verdict:** CORRECT.

---

## 3. Grammar Node Types Verification

### 3.1 Python Grammar (tree-sitter-python)

| PRD Claim (REQ-044) | Actual Node Type | Verdict |
|---|---|---|
| `class_definition` | `class_definition` | CORRECT |
| `function_definition` | `function_definition` | CORRECT |
| decorated definitions | `decorated_definition` (wraps decorator + definition) | CORRECT |

**Fields confirmed (Context7 corpus tests):**
- `function_definition` has fields: `name` (identifier), `parameters`, `body` (block), `return_type`
- `class_definition` has fields: `name` (identifier), `body`, `superclasses`
- `decorated_definition` wraps `decorator` + the actual definition

**ISSUE-3 (INFO):** REQ-044 says "Query for...decorated definitions (@property, @staticmethod)". In tree-sitter-python, a decorated function is a `decorated_definition` node containing `decorator` children and one `function_definition` or `class_definition` child. The query pattern would be:
```
(decorated_definition
  (decorator) @decorator
  (function_definition name: (identifier) @name))
```
This is implied but not explicitly shown. No fix needed -- implementors should know this.

### 3.2 TypeScript Grammar (tree-sitter-typescript)

| PRD Claim (REQ-044) | Expected Node Type | Verdict |
|---|---|---|
| `interface_declaration` | `interface_declaration` | CORRECT (standard TS grammar) |
| `type_alias_declaration` | `type_alias_declaration` | CORRECT (standard TS grammar) |
| `export_statement` | `export_statement` | CORRECT |
| `function_declaration` | `function_declaration` | CORRECT |
| `lexical_declaration` | `lexical_declaration` (const/let) | CORRECT |

### 3.3 C# Grammar (tree-sitter-c-sharp)

| PRD Claim (REQ-044) | Expected Node Type | Verdict |
|---|---|---|
| `class_declaration` | `class_declaration` | CORRECT |
| `interface_declaration` | `interface_declaration` | CORRECT |
| `method_declaration` | `method_declaration` | CORRECT |
| `namespace_declaration` | `namespace_declaration` | CORRECT |

### 3.4 Go Grammar (tree-sitter-go)

| PRD Claim (REQ-044) | Expected Node Type | Verdict |
|---|---|---|
| `function_declaration` | `function_declaration` | CORRECT |
| `type_declaration` | `type_declaration` | CORRECT |
| `method_declaration` | `method_declaration` | CORRECT |

---

## 4. Code Analysis Patterns

### 4.1 Symbol Extraction (REQ-043)

**Approach:** Use tree-sitter queries to find all symbol definitions, extract metadata.

**Assessment:** Sound approach. Using `QueryCursor.captures()` with capture names like `@function.name` is the standard way to extract symbols from AST. The pattern of delegating to language-specific parsers (REQ-044) is correct for handling grammar differences.

**ISSUE-5 (LOW):** REQ-046 says "Add edges for...function calls (relation='calls')" but doesn't specify how call sites are detected from AST. For Python, calls are `call` nodes with a `function` field. For TypeScript, they are `call_expression` nodes. Mapping a call to the correct target symbol requires import resolution + name resolution, which is non-trivial. The PRD should acknowledge this complexity or specify a "best-effort" matching strategy.

### 4.2 Import Resolution (REQ-045)

**Assessment:** Comprehensive for Python and TypeScript. The Python import patterns (relative, absolute) and TypeScript patterns (relative, @/ alias, tsconfig.json paths) cover the common cases.

**ISSUE-6 (INFO):** No C# (`using` statements) or Go (`import` blocks) import resolution is specified. The sample codebase only has Python and TypeScript files, so this is acceptable. C# and Go parsers extract symbols but don't resolve imports -- this is a scope limitation, not a bug.

### 4.3 Dead Code Detection (REQ-048)

**Assessment:** The in_degree==0 approach is sound for file-level and symbol-level graphs. The entry point exclusion list is comprehensive (dunder methods, FastAPI lifecycle, test functions, CLI entry points, Pydantic validators). Confidence classification (high/medium/low) is reasonable.

### 4.4 Dependency Graph (REQ-046, REQ-047)

**Assessment:** Using NetworkX DiGraph with file paths as nodes is correct. The TECH-018 note about `edges="edges"` parameter is accurate -- NetworkX changed the default serialization key from "links" to requiring explicit "edges" parameter.

### 4.5 Semantic Search (REQ-052, REQ-053, REQ-054)

**Assessment:** ChromaDB integration is correctly specified. Using symbol signature + docstring + code body as document text for embedding is reasonable. The metadata filter patterns (TECH-021, TECH-025) are accurate for ChromaDB's query API.

---

## 5. All Issues Summary

### MEDIUM (2)

| ID | Location | Issue | Suggested Fix |
|---|---|---|---|
| ISSUE-1 | REQ-042 | Generic `Language(tree_sitter_xxx.language())` doesn't apply to TypeScript (which exports `language_typescript()` / `language_tsx()` not `language()`). TECH-017 documents this correctly but REQ-042 should cross-reference. | Add to REQ-042: "(see TECH-017 for TypeScript exception using language_typescript/language_tsx)" |
| ISSUE-2 | REQ-043 | The required imports (`from tree_sitter import Query, QueryCursor`) are not shown. Only `Language` and `Parser` imports are mentioned elsewhere. Implementors need to know about the `Query` and `QueryCursor` classes. | Add explicit import list to REQ-043: "Import Query and QueryCursor from tree_sitter" |

### LOW (3)

| ID | Location | Issue |
|---|---|---|
| ISSUE-5 | REQ-046 | Call graph construction for "calls" relation is mentioned but the AST detection strategy (finding `call` / `call_expression` nodes and mapping to symbols) is not specified. |
| ISSUE-7 | REQ-001 | Package name `tree-sitter-c-sharp` maps to Python import `tree_sitter_c_sharp`. The hyphen-to-underscore conversion and "c-sharp" -> "c_sharp" mapping could confuse implementors. |
| ISSUE-8 | REQ-044 | No query patterns are shown as examples. Adding one example query string per language would help implementors. |

### INFO (4)

| ID | Location | Note |
|---|---|---|
| ISSUE-3 | REQ-044 | Decorated definitions in Python use `decorated_definition` wrapper node -- implicit but could be made explicit. |
| ISSUE-4 | REQ-043 | Query constructor signature `Query(language, source_string)` not documented. |
| ISSUE-6 | REQ-045 | C# and Go import resolution not specified (acceptable -- sample codebase is Python + TypeScript only). |
| ISSUE-9 | General | The old API (`Query.captures()`, `Query.matches()`) was removed in v0.23.0. The PRD correctly uses the v0.25.x `QueryCursor` API. This is a documentation win -- no migration issues. |

---

## 6. Verified Claims Checklist

### tree-sitter Python Bindings
- [x] Package name: `tree-sitter` (pip install tree-sitter) -- CORRECT
- [x] `Parser()` class -- construction with language, `.language` property -- CORRECT
- [x] `Language()` class -- `Language(tree_sitter_xxx.language())` pattern -- CORRECT (with TypeScript exception)
- [x] `Node` class -- type, text (bytes), children, named_children, start_point, end_point -- CORRECT
- [x] `Tree` class -- root_node -- CORRECT
- [x] Query syntax: `(function_definition name: (identifier) @function.name)` -- CORRECT
- [x] Pattern matching: `QueryCursor(query).captures(root_node)` returns `dict[str, list[Node]]` -- CORRECT

### Language Grammar Packages
- [x] Grammars are separate packages (tree-sitter-python, tree-sitter-typescript, etc.) -- CORRECT
- [x] Loading: `Language(tree_sitter_python.language())` for most; `Language(tree_sitter_typescript.language_typescript())` for TS -- CORRECT
- [x] TypeScript has two sub-languages: `language_typescript()` and `language_tsx()` -- CORRECT
- [x] Version pinning matches latest stable releases -- CORRECT
- [x] v0.23.0 had breaking changes (Query.captures/matches removed); v0.25.0 added QueryCursor -- PRD uses correct v0.25.x API

### Code Analysis Patterns
- [x] Function/class extraction from AST via queries -- CORRECT approach
- [x] Import resolution (Python relative/absolute, TypeScript relative/alias) -- CORRECT
- [x] Dependency graph via NetworkX DiGraph -- CORRECT
- [x] Dead code detection via in_degree==0 with entry point filtering -- CORRECT
- [x] Multi-language support via language-specific parser modules -- CORRECT architecture

### Build 1 Codebase Intelligence
- [x] File discovery and parsing pipeline (ASTParser.parse_file) -- CORRECT
- [x] Language detection from extension -- CORRECT
- [x] Symbol table construction (SymbolExtractor + SymbolDB) -- CORRECT
- [x] Cross-reference building (ImportResolver + GraphBuilder) -- CORRECT
- [x] Cache/performance: ChromaDB for semantic, SQLite for structured, NetworkX snapshots for graph -- CORRECT

---

## 7. Context7 Research Summary

### Sources Consulted
1. **py-tree-sitter README** (Context7 `/tree-sitter/py-tree-sitter`): Parser construction, Language loading, Node properties, Query/QueryCursor API, captures/matches usage
2. **tree-sitter official docs** (Context7 `/websites/tree-sitter_github_io_tree-sitter`): Query syntax, tagging examples, grammar definitions
3. **tree-sitter-python grammar** (Context7 `/tree-sitter/tree-sitter-python`): Python node types (function_definition, class_definition, decorated_definition, import_from_statement)
4. **PyPI pages**: Version verification for all 5 packages
5. **GitHub bindings source**: `__init__.py` files for tree-sitter-typescript, tree-sitter-c-sharp, tree-sitter-go, tree-sitter-python -- verified exact export names

### Key API Facts (v0.25.2)
```python
# Language loading
import tree_sitter_python
from tree_sitter import Language, Parser, Query, QueryCursor

PY_LANGUAGE = Language(tree_sitter_python.language())

# Parser
parser = Parser(PY_LANGUAGE)
tree = parser.parse(b"def foo(): pass")

# Node access
root = tree.root_node       # Node
root.type                   # "module"
root.children[0].type       # "function_definition"
root.children[0].text       # b"def foo(): pass" (BYTES!)
root.start_point            # (0, 0) -- 0-indexed!

# Query + QueryCursor (v0.25.x API)
query = Query(PY_LANGUAGE, "(function_definition name: (identifier) @func.name)")
cursor = QueryCursor(query)
captures = cursor.captures(tree.root_node)  # dict[str, list[Node]]
matches = cursor.matches(tree.root_node)    # list[tuple[int, dict[str, list[Node]]]]

# TypeScript special case
import tree_sitter_typescript
TS_LANG = Language(tree_sitter_typescript.language_typescript())   # .ts
TSX_LANG = Language(tree_sitter_typescript.language_tsx())         # .tsx
```

---

## 8. Recommended PRD Fixes

### Fix 1 (MEDIUM): REQ-042 TypeScript cross-reference
**Current:** "Load appropriate tree-sitter grammar via Language(tree_sitter_xxx.language())."
**Replace with:** "Load appropriate tree-sitter grammar via Language(tree_sitter_xxx.language()). Note: TypeScript uses language_typescript() and language_tsx() instead of language() -- see TECH-017."

### Fix 2 (MEDIUM): REQ-043 explicit imports
**Current:** "Use tree-sitter Query with language-specific patterns..."
**Add before QueryCursor mention:** "Import Query and QueryCursor from tree_sitter (`from tree_sitter import Query, QueryCursor`)."

### Fix 3 (LOW): REQ-001 import name note
**Add to REQ-001 after tree-sitter-c-sharp pin:** Add a comment or note: "Python import name: tree_sitter_c_sharp (note underscore conversion from hyphenated package name)."
