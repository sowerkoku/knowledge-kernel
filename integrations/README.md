# Knowledge Kernel Integrations

Integration wrappers for connecting the Knowledge Kernel to specific agent frameworks.

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

The knowledge-kernel core is **framework-agnostic**.

Integrations provide:
- Framework-specific wrappers
- Tool registration
- Skill definitions

The core (`cmdb/`) never knows about specific frameworks.