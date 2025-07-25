# Coding Standards

## Package Management

This project uses `uv` as the package manager. All package installation and dependency management should be done through `uv`.

### Common Commands

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Install with specific provider dependencies
uv pip install -e ".[openai]"

# Install from lock file (recommended for consistent environments)
uv sync

# Run tests
uv run pytest

# Run tests with verbose output
uv run pytest -sv --log-cli-level=0
```

## Testing

All tests should be run using `uv run pytest`:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unified/test_base.py

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/llmgine
```

## Code Quality Tools

All code quality tools should be run through `uv`:

```bash
# Linting
uv run ruff check src/

# Formatting
uv run ruff format src/

# Type checking
uv run mypy

# Auto-fix lint issues
uv run ruff check --fix src/
```

## Development Workflow

1. Always use `uv sync` to ensure dependencies are up to date
2. Run tests with `uv run pytest` before committing
3. Use `uv run` prefix for all Python tool commands
4. Follow the existing code patterns and conventions in the codebase

## Python Version

- Python 3.11+ is required
- All code should be compatible with Python 3.11+

## Code Style

- Line length: 90 characters
- Use type hints for all function signatures
- Follow PEP 8 with Ruff configuration
- Async by default for all I/O operations
- Use Pydantic for data models
- Strict type checking with MyPy

## Import Organization

1. Standard library imports
2. Third-party imports
3. Local application imports

Each group should be alphabetically sorted and separated by a blank line.

## Documentation

- All public functions and classes must have docstrings
- Use Google-style docstrings
- Include type information in function signatures, not docstrings
- Document exceptions that can be raised