# Tech Stack

## Core Technologies

### Python
- **Version**: 3.11+
- **Package Manager**: uv
- **Build System**: Hatchling (PEP 517)

### Core Libraries
- **Pydantic**: Data validation and settings management
- **httpx**: Async HTTP client for API calls
- **Rich**: Terminal formatting and progress displays
- **asyncio**: Asynchronous programming

### Development Tools
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **Ruff**: Linting and code formatting
- **MyPy**: Static type checking
- **pre-commit**: Git hooks for code quality

### LLM Providers
- **OpenAI**: Via httpx (no SDK)
- **Anthropic**: Via httpx (no SDK)
- **Google Gemini**: Via httpx (no SDK)

### Frontend (Observability GUI)
- **Vite**: Build tool
- **TypeScript**: Type-safe JavaScript
- **React**: UI framework
- **Tailwind CSS**: Styling

## Architecture Patterns

### Message Bus
- Command/Event pattern
- Session-based isolation
- Automatic handler cleanup

### Engines
- Base engine class for standardization
- Command handlers for logic
- Event emission for observability

### Tools
- Declarative function registration
- Automatic schema generation
- Provider-specific adaptations

## Development Environment

### Required Environment Variables
- `OPENAI_API_KEY`: For OpenAI API access
- `ANTHROPIC_API_KEY`: For Anthropic API access
- `GEMINI_API_KEY`: For Google Gemini API access

### Directory Structure
- `src/llmgine/`: Core library code
- `programs/`: Example applications
- `tests/`: Test suite
- `docs/`: Documentation
- `logs/`: Event logs (gitignored)