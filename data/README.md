# Data Directory — Production Dataset (NOT in version control)

**This directory is intentionally empty in the repository.**

Production datasets live externally (e.g., `~/knowledge/knowledge-kernel/`) and are excluded from git via `.gitignore`.

## Why?

**Code ≠ Data.** This repository contains:
- The Knowledge Kernel API (`cmdb/`)
- Documentation (`docs/`)
- Integration wrappers (`integrations/`)
- Canonical examples (`examples/`)

Your infrastructure facts (the dataset) are **production data**, not code. They:
- Change frequently (daily discoveries, updates)
- Are environment-specific (your infra ≠ mine)
- May contain sensitive details (hostnames, IPs, configurations)

## Location

Default dataset path: `~/knowledge/knowledge-kernel/`

Configure via env var:
```bash
export CMDB_DATA_DIR=~/knowledge/knowledge-kernel
```

## Structure (when populated)

```
data/
├── assets/       # Hardware: servers, devices, routers
├── software/     # Applications, services, databases
├── endpoints/    # Network: IPs, networks, ports
├── data/         # Configurations, profiles, secrets
├── agents/       # AI agents and their profiles
├── automation/   # Cron jobs, CI/CD pipelines
├── procedures/   # Runbooks, operational procedures
├── projects/     # Active projects with dependencies
└── secrets/      # Encrypted credentials
```

## Getting Started

Copy canonical examples to bootstrap your dataset:

```bash
cp examples/asset-example.yaml ~/knowledge/knowledge-kernel/assets/my-server.yaml
cp examples/software-example.yaml ~/knowledge/knowledge-kernel/software/my-app.yaml
```

Then edit with your actual infrastructure facts.

⚠️ **DO NOT commit `data/` to version control** — it is gitignored for a reason.
