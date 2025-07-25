# Source Tree

## Project Structure

```
llmgine/
├── src/llmgine/              # Core library
│   ├── bus/                  # Message bus implementation
│   │   ├── bus.py           # Core message bus
│   │   └── listener.py      # Event listener utilities
│   ├── database/             # Database utilities
│   ├── llm/                  # LLM-related components
│   │   ├── context/         # Context management
│   │   ├── engine/          # Engine implementations
│   │   ├── models/          # Model wrappers
│   │   ├── providers/       # Legacy provider implementations
│   │   └── tools/           # Tool system
│   │       └── mcp/         # MCP tool support
│   ├── messages/             # Command and event definitions
│   ├── observability/        # Observability infrastructure
│   │   └── handlers/        # Event handlers
│   ├── orchestrator/         # Provider orchestration layer
│   ├── prompts/              # Prompt templates
│   ├── providers/            # New modular provider architecture
│   │   ├── base.py          # Base provider interface
│   │   ├── utils.py         # Provider utilities
│   │   ├── openai/          # OpenAI provider implementation
│   │   ├── anthropic/       # Anthropic provider implementation
│   │   └── gemini/          # Gemini provider implementation
│   ├── ui/                   # User interface components
│   │   └── cli/             # CLI utilities
│   └── unified/              # Unified LLM interface
│       └── models.py        # Core unified data models
├── programs/                 # Example applications
│   ├── engines/             # Example engine implementations
│   └── observability-gui/   # React-based log viewer
├── tests/                    # Test suite
│   ├── unified/             # Tests for unified interface
│   └── ...                  # Other test modules
├── docs/                     # Documentation
│   ├── architecture/        # Architecture docs
│   ├── epics/               # Development epics
│   ├── stories/             # Development stories
│   │   └── backlog/         # Backlog stories
│   └── prd.md              # Product requirements
├── logs/                     # Event logs (gitignored)
├── scripts/                  # Development scripts
├── pyproject.toml           # Project configuration
├── uv.lock                  # Dependency lock file
├── Makefile                 # Development shortcuts
├── CLAUDE.md                # Claude Code instructions
└── setup-dev.sh             # Development setup script
```

## Key Directories

### src/llmgine/bus/
Core message bus implementation with command/event handling.

### src/llmgine/llm/
LLM-related components including engines, models, legacy providers, and tools.

### src/llmgine/providers/
New modular provider architecture with implementations for OpenAI, Anthropic, and Gemini. Each provider is self-contained with its own models and client.

### src/llmgine/unified/
Unified data models that provide a common interface across all providers.

### src/llmgine/orchestrator/
Provider orchestration layer that manages provider selection and routing.

### src/llmgine/observability/
Observability infrastructure for monitoring and debugging.

### src/llmgine/messages/
Pydantic models for commands and events used throughout the system.

### programs/
Example applications demonstrating framework usage.

### tests/
Comprehensive test suite with async support.

## File Naming Conventions

- Python modules: `lowercase_with_underscores.py`
- Test files: `test_<module_name>.py`
- Documentation: `kebab-case.md`
- Configuration: `dot.files` or `kebab-case.yaml`