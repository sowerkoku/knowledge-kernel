# Runtime Discovery — Pattern Reference

## Concept

Discovery skill that observes real infrastructure state and produces evidence to update the Knowledge Kernel.

**Not** a validation/correction skill. **Not** direct modification. A human-approved evidence pipeline.

```
Observed Reality
       ↓
   SSH + ss
   Docker inspect
   HTTP probe
       ↓
Discovery (evidence)
       ↓
Knowledge Kernel (diff)
       ↓
Human approval
       ↓
Fact update
```

## Renamed from

`registry-network-validation` → `runtime-discovery`

The old name implies "correct bad data". The new name implies "discover what is true".

## Entity Model for Discovery

```
Asset  (app-server-01)
   ▲
   │ runs_on
   │
Software  (ollama)
   │
   │ exposes
   ▼
Endpoint  (ollama-api: 192.168.10.10:11434)
```

Each level discovered separately:

| Level | Discovery method |
|---|---|
| Asset | SSH hostname, uname, hardware info |
| Software | Docker ps, systemd units, process list |
| Endpoint | `ss -tlnp`, HTTP probe, port scan |

## Endpoint Discovery Pattern

```bash
# 1. List listening ports on asset
ssh user@ASSET "ss -tlnp"

# 2. HTTP probe to identify service
ssh user@ASSET "curl -s --max-time 2 http://localhost:PORT | grep -E '<title'"

# 3. Docker port mapping
ssh user@ASSET "docker ps --format '{{.Names}}\t{{.Ports}}'"
```

## Output: Evidence, not Modifications

Discovery produces a **diff**, not a commit:

```python
{
    "observed": [
        {"id": "ollama-api", "host": "192.168.10.10", "port": 11434, "protocol": "http"},
    ],
    "in_kernel": [
        {"id": "ollama-api", "host": "localhost", "port": 11434, "protocol": "http"},  # WRONG
    ],
    "proposed_changes": [
        {"field": "metadata.host", "from": "localhost", "to": "192.168.10.10", "entity": "ollama-api"}
    ]
}
```

**Never auto-commit.** Present diff to human → approval → update.

## Relationship to agent-cmdb

Discovery feeds the Knowledge Kernel but is separate from it:

- agent-cmdb: stores facts + evidence + freshness
- Runtime Discovery: observes reality + produces evidence
- Integration: discovery output becomes `cmdb_assert()` calls

## Naming Convention for Skills

Start with `runtime-discovery` as umbrella:

```
runtime-discovery/
├── SKILL.md
├── references/
│   ├── endpoint-discovery.md   # first module implemented
│   ├── asset-discovery.md      # future
│   └── protocol-discovery.md    # future
└── scripts/
    ├── ss-probe.sh
    └── http-probe.sh
```

Future modules (not implemented yet):
- `asset-discovery`: hardware, OS, kernel, storage
- `volume-discovery`: mount points, NFS,tmpfs
- `certificate-discovery`: TLS certs and expiry
- `socket-discovery`: Unix domain sockets