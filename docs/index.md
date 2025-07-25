# LLMgine Documentation

Welcome to the LLMgine documentation. LLMgine is a pattern-driven framework for building production-grade, tool-augmented LLM applications in Python.

## Documentation Structure

### 📚 User Guides
- [Unified LLM Interface Guide](./guides/unified-llm-interface-guide.md) - How to use the unified interface
- [Observability Cookbook](./guides/observability-cookbook.md) - Practical recipes and examples

### 🏗️ Architecture
- [Source Tree](./architecture/source-tree.md) - Project structure overview
- [Provider Architecture](./architecture/provider-architecture.md) - Modular provider design
- [Observability Architecture](./observability-architecture.md) - Observability system design
- [Tech Stack](./architecture/tech-stack.md) - Technology choices
- [Coding Standards](./architecture/coding-standards.md) - Development guidelines

### 🚀 Development
- [Product Requirements Document](./development/prd.md) - Project vision and roadmap
- [Project Status](./development/project-status.md) - Current implementation status
- [Stories](./stories/) - Development stories and epics
- [Epics](./epics/) - High-level feature epics

### 📦 Migration
- [Observability Migration Guide](./migration/observability-migration-guide.md) - Upgrading from EventLogWrapper

### 🔧 Component Documentation
- [Message Bus](../src/llmgine/bus/README.md) - Event and command bus architecture
- [Observability System](../src/llmgine/observability/README.md) - Standalone observability
- [Tools System](../src/llmgine/llm/tools/README.md) - Function calling and tool registration

## Current Focus

### Active Development
- [Story 1.3: Unified LLM Interface](./stories/story-1-3-unified-llm-interface.md) - **Current Focus**
- [Story 1.4: Refactor Tool/Context Managers](./stories/story-1-4-refactor-tool-context-managers.md) - Next priority

### Recently Completed
- [Story 1.1: Standalone Observability Module](./stories/story-1-1-opentelemetry-handler.md) ✅
- [Story 1.2: Enhanced Message Bus](./stories/story-1-2-enhance-message-bus.md) ✅

### Epic 2: Provider Response Management
- [Epic Overview](./epics/epic-0002-provider-response-management.md)
- [Story 2.1: Response Recording Framework](./stories/story-2-1-response-recording-framework.md)
- [Story 2.2: Base Response Redesign](./stories/story-2-2-base-response-redesign.md)
- [Story 2.3-2.6: Provider Implementations](./stories/) 
- [Story 2.7: Migration and Cleanup](./stories/story-2-7-migration-and-cleanup.md)

## Quick Links

- [Main README](../README.md) - Getting started and overview
- [CLAUDE.md](../CLAUDE.md) - AI assistant instructions
- [Makefile Commands](../Makefile) - Development shortcuts
- [PyProject Configuration](../pyproject.toml) - Package configuration

## Getting Help

- Check the [troubleshooting guide](./guides/troubleshooting.md) for common issues
- Review the [API documentation](./api/) for detailed reference
- See the [examples](../programs/) for working code samples