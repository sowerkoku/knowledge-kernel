# Agent-CMDB Integrations

Integration wrappers for connecting Agent-CMDB to specific agent frameworks.

## Directory Structure

```
integrations/
├── hermes/           # Hermes Agent integration (first consumer)
│   ├── SKILL.md
│   ├── tools/
│   └── tests/
├── openclaw/         # Future: OpenClaw integration
├── langgraph/        # Future: LangGraph integration
└── autogen/          # Future: AutoGen integration
```

## Design Principle

Agent-CMDB core is **framework-agnostic**.

Integrations provide:
- Framework-specific wrappers
- Tool registration
- Skill definitions

The core (`cmdb/`) never knows about specific frameworks.