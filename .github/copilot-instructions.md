# BA-Agent API - GitHub Copilot Instructions

> These instructions apply to the FastAPI backend (BaAgentApi).

## Project Overview

- **Project**: BA-Agent - Business Analysis Agent Backend API
- **Tech Stack**: Python 3.12, FastAPI, LangGraph, LangChain, Google Gemini AI, MongoDB, ChromaDB
- **Architecture**: Multi-Agent Orchestration with Dynamic Graph Assembly

## Project Structure

```
BaAgentApi/
├── main.py                  # FastAPI app entry point
├── routers/                 # API endpoints
├── graphs/                  # LangGraph workflow definitions
├── graph_nodes/             # Agent and supervisor nodes
├── tools/                   # Dynamic tool creation
├── mongodb/actions/         # Database operations
├── models/                  # Pydantic models
└── utils/                   # Helper utilities
```

## Core Principles

### SOLID
- **SRP**: One reason to change per module
- **OCP**: Database-driven configuration for extensibility
- **LSP**: Subtypes substitutable for base types
- **ISP**: Small, focused interfaces
- **DIP**: Depend on abstractions

### Clean Code
- Functions under 20 lines (Python allows more than TS)
- Files under 200 lines
- Early returns, avoid deep nesting
- Type hints for all function signatures
- Descriptive names with snake_case

### Naming Conventions
- Files/Directories: `snake_case`
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `SCREAMING_SNAKE_CASE`
- Private functions: `_leading_underscore`

## Quick Rules

- Use async/await for I/O operations
- Type hints required for all public functions
- Use Pydantic models for data validation
- Handle errors with try-except in routes
- Use dependency injection for MongoDB client
- Log important operations (use logging module)

## Git Conventions

```
feat: add new feature
fix: bug fix
refactor: code refactoring
docs: documentation
test: add tests
```

---

## 🧹 Dead Code Cleaner - Auto-Trigger Mode (Python/FastAPI)

### When to Activate

**AUTOMATICALLY** scan for and suggest dead code removal when:
- User mentions: "cleanup", "clean up", "clean code", "optimize"
- User asks about: "unused", "dead code", "remove obsolete"
- During refactoring: "refactor", "remove legacy"
- After dependencies updated or features removed
- Before production deployments

### Detection Strategy for Python/FastAPI

#### 1. Unused Imports
```bash
# Find potentially unused imports
rg "^(from|import)\s+" --type py | \
  while read line; do
    module=$(echo "$line" | grep -oP "(from|import)\s+\K\w+")
    count=$(rg "\b$module\b" --type py --count)
    [ "$count" -lt 2 ] && echo "Potentially unused: $line"
  done
```

#### 2. Unused Functions
```python
# Functions defined but never called
# Search: def function_name
# Verify: function_name( not found elsewhere
rg "^def\s+(\w+)" --type py -r '$1' | \
  while read func; do
    [ $(rg "\b$func\(" --type py --count) -lt 2 ] && echo "Unused: $func"
  done
```

#### 3. Unused Classes
```bash
# Classes defined but never instantiated
rg "^class\s+(\w+)" --type py -r '$1' | \
  while read cls; do
    rg "\b$cls\(" --type py
  done
```

#### 4. Unused API Endpoints
```bash
# FastAPI routes not called by frontend
# Check routers/ for @router.get/@router.post
rg "@router\.(get|post|put|delete)\(" routers/ --type py
```

#### 5. Unused Dependencies
```bash
# Check requirements.txt vs actual imports
# List all packages not imported in codebase
```

#### 6. Unused MongoDB Operations
```bash
# Database operations in mongodb/actions/ not called
rg "^def\s+" mongodb/actions/ --type py
```

### Verification Protocol

**Before suggesting ANY removal:**

1. **Multi-pattern search**:
   ```bash
   # For element "example_function"
   rg "\bexample_function\b" --type py
   rg "['\"\\`]example_function['\"\\`]" --type py
   rg "example_function" .
   ```

2. **Check imports across modules**:
   ```bash
   rg "from .* import.*example_function" --type py
   rg "import.*example_function" --type py
   ```

3. **Check dynamic usage**:
   ```bash
   # String-based imports, getattr, __import__
   rg "getattr|__import__|importlib" --type py
   ```

4. **Check test files**:
   ```bash
   find . -name "*test*.py" | xargs rg "example_function"
   ```

5. **Check configuration**:
   ```bash
   rg "example_function" *.json *.yml *.yaml *.toml *.ini
   ```

### Safe Removal Checklist

Generate report in this format:

```markdown
## 🗑️ Dead Code Analysis - Backend (Python)

### Summary
- **Unused imports**: X found
- **Unused functions**: X found
- **Unused classes**: X found
- **Unused routes**: X found
- **Unused dependencies**: X packages
- **Estimated cleanup**: X% LOC reduction

### High Confidence Removals

#### Unused Imports (X)
1. **Module**: `unused_module` in `routers/example.py:5`
   - Verification: ✅ Not referenced in file
   - Risk: SAFE (flake8/pylint will catch errors)

#### Unused Functions (X)
1. **Function**: `helper_function()` in `utils/helpers.py:45`
   - Size: X lines
   - Last modified: DATE
   - Verification: ✅ No calls found in codebase
   - Risk: LOW

#### Unused Classes (X)
1. **Class**: `LegacyProcessor` in `utils/legacy.py:12`
   - Size: X lines
   - Verification: ✅ No instantiations found
   - Risk: LOW

#### Unused API Routes (X)
1. **Route**: `GET /api/old-endpoint` in `routers/deprecated.py:89`
   - Verification: ⚠️ Check frontend for calls
   - Risk: MEDIUM (requires frontend verification)

#### Unused Dependencies (X)
1. **Package**: `unused-package==1.2.3` in `requirements.txt`
   - Verification: ✅ No imports found
   - Risk: LOW

### Recommended Actions
- [ ] Review list above
- [ ] Remove unused imports (safe - Python will error on missing imports)
- [ ] Remove unused functions/classes (verify with tests)
- [ ] Remove unused routes (verify frontend doesn't call them)
- [ ] Remove unused packages from requirements.txt

### Safety Notes
- All items verified with multi-pattern search
- No references found in code, tests, or configs
- Recommend running `pytest && flake8 .` after removal
- Verify Docker build succeeds after dependency removal
```

### Execution Guidelines

1. **Always ask for approval** before removing code
2. **Remove one category at a time**:
   - Unused imports (safest)
   - Unused helper functions
   - Unused classes
   - Unused routes (verify with frontend team)
   - Unused dependencies (test in Docker)

3. **Run verification after each removal**:
   ```bash
   pytest                    # Run tests
   flake8 .                  # Check for errors
   python main.py --help     # Verify app starts
   ```

4. **Never remove**:
   - Files in `venv/`, `__pycache__/`, `.pytest_cache/`
   - Configuration files (`.env`, `requirements.txt` entries actively used)
   - Migration files
   - Database schema definitions
   - LangGraph state models (even if seemingly unused)
   - MongoDB connection singletons

### Python-Specific Patterns

#### Find Unused Module-Level Variables
```python
# Variables defined but never used
rg "^[A-Z_]+ = " --type py  # Constants
```

#### Find Unused Private Functions
```python
# Private functions (prefixed with _) not called within module
rg "^def _\w+" --type py
```

#### Find Unused Pydantic Models
```python
# Models defined but never used for validation
rg "class \w+\(BaseModel\):" --type py
```

#### Find Dead Conditional Branches
```python
# if False blocks, unreachable code after return
rg "if False:|if 0:" --type py
```

### FastAPI-Specific Rules

- **Unused Middleware**: Middleware functions not registered in app
- **Unused Dependencies**: FastAPI Depends() functions not used in routes
- **Unused Routers**: Router instances not included in main app
- **Unused Pydantic Schemas**: Request/response models not used in endpoints

### LangGraph-Specific Considerations

**DO NOT REMOVE** without verification:
- State model fields (may be used dynamically)
- Node functions registered in graph (check graph compilation)
- Tool functions referenced in MongoDB (database-driven)
- Checkpointer configurations

### MongoDB-Driven Architecture Warning

⚠️ **CRITICAL**: This codebase uses **database-driven configuration**

- Agents, tools, and workflows defined in MongoDB, not code
- A function may appear unused but is called dynamically via DB lookup
- **Always check MongoDB collections** before removing:
  - `tools` collection for tool/agent references
  - `agents` collection for agent configurations
  - Configuration documents that reference code by string name

**Verification steps**:
```bash
# Check if function name appears in MongoDB
mongo mastraDB2 --eval "db.tools.find({}, {toolName: 1, agentToolName: 1})"
mongo mastraDB2 --eval "db.agents.find()"
```

### Integration with Development Flow

**During Code Review**: Suggest unused code removal in PR comments
**During Refactoring**: Proactively scan affected modules
**Before Commits**: Quick scan with `flake8 --select=F401` (unused imports)
**After Dependency Updates**: Check `requirements.txt` vs actual imports

---

**Note**: This dead code cleaner runs in advisory mode only. Always present findings to the developer for approval before making changes. For database-driven code, verify MongoDB collections before suggesting removal.
