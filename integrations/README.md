# Knowledge Kernel Integrations

Adaptors that connect the Knowledge Kernel to specific external
platforms or agents.

## Directory Structure

```
knowledge-kernel/
├── kernel/           # The Knowledge Kernel itself (framework-agnostic)
├── consumers/         # Native consumers of the Kernel public API
│   ├── inspector/    # Knowledge Inspector — rule-based evaluation
│   └── telemetry/    # Telemetry — metrics and grounding logger
├── integrations/     # Platform / agent-specific adapters
│   ├── hermes/       # Hermes Agent integration
│   ├── openclaw/     # (future)
│   ├── zeroclaw/     # (future)
│   └── ...
└── docs/
```

## Design Principle

The distinction between **consumers** and **integrations** matters:

- **consumers/** — components built on the Kernel's public API. They are
  framework-agnostic and could run from CI, terminal, GitHub Actions,
  or any agent. Inspector and Telemetry belong here.

- **integrations/** — adapters for specific external platforms. They
  depend on the external platform and live here because of that
  dependency. Hermes, OpenClaw, etc. belong here.

Moving a component from `integrations/` to `consumers/` is a
**statement about its architecture**: it means the component no longer
depends on a specific external platform.