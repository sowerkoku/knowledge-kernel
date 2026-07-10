# knowledge-kernel Data Directory

This directory contains your infrastructure facts as YAML files.

## Structure

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

## Adding Entities

Create YAML files in the appropriate category folder:

```yaml
schema_version: 1
id: my-server
kind: asset
metadata:
  name: My Server
  description: Physical server in datacenter
  hostname: server-01
  cpu: Intel Xeon
  ram: 32GB
status: operational
relations: []
criticality:
  business: high
  operational: high
  technical: medium
```

## Security

⚠️ **DO NOT commit this directory to version control**

The `data/` directory is excluded from git via `.gitignore`.
Your infrastructure data is sensitive — keep it private.

## Examples

See `../examples/entities/` for example entity formats.
