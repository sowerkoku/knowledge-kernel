# Network Validation Pattern for Registry

## Purpose

Validate and update `network.host` and `network.port` fields in Registry YAML files by querying the actual infrastructure via SSH. Prevents stale data (localhost, outdated ports, missing fields).

## Audit Trigger

Run this audit when:
- User reports "connection refused" to a service that Registry says is operational
- You notice multiple services with same `network.port` on same host
- Before major infrastructure changes (shutdown, migration)
- Periodic validation (quarterly recommendation)

## Validation Workflow

### Step 1: Extract claimed network data from Registry

```bash
cd ~/.hermes/skills/registry
python3 -c "
from registry import registry_list, registry_get
for s in registry_list('software'):
    e = registry_get(s['id'])
    net = e.get('network', {})
    runs = e.get('relations', {}).get('runs_on', [])
    print(f\"{s['id']:20} | runs_on={str(runs):25} | host={net.get('host', 'N/A'):16} | port={net.get('port', 'N/A')}\")
"
```

**Red flags:**
- `host: localhost` for services that run on remote assets
- Multiple services with same port on same host (potential conflict)
- `port: null` or missing network section for operational services

### Step 2: SSH into target asset and query reality

```bash
# For each unique runs_on asset:
ssh carlos@<asset-ip> "ss -tlnp 2>/dev/null | grep LISTEN"
```

**Alternative if ss unavailable:**
```bash
ssh carlos@<asset-ip> "netstat -tlnp 2>/dev/null | grep LISTEN"
```

### Step 3: Identify service per port via curl

```bash
# For each listening port, identify the service:
ssh carlos@<asset-ip> "curl -s --max-time 2 http://localhost:<port> 2>&1 | grep -o '<title>[^<]*</title>'"

# For HTTPS:
ssh carlos@<asset-ip> "curl -s -k --max-time 2 https://localhost:<port> 2>&1 | grep -o '<title>[^<]*</title>'"
```

### Step 4: Docker containers inspection

For services running in containers:

```bash
# List all containers and their port mappings
ssh carlos@<asset-ip> "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Check network mode (host vs bridge)
ssh carlos@<asset-ip> "docker inspect --format '{{.Name}} {{.HostConfig.NetworkMode}}' \$(docker ps -aq)"
```

**Key insight:** Containers with `--network=host` listen directly on host ports (no port mapping).

### Step 5: Update YAML files

For each discrepancy found:

```bash
# Example: phpmyadmin was 8080, reality is 80
cd /home/carlos/registry/software
# Edit phpmyadmin.yaml:
#   network:
#     host: 192.168.1.54   # IP from runs_on asset
#     port: 80             # Verified port
```

**Git commit message:**
```
[phpmyadmin] Update port 8080→80
- Verified via curl on 192.168.1.54: response shows <title>phpMyAdmin</title> on port 80
- Port 8080 actually serves OpenWebUI
```

## Common Pitfalls (from Jun 2026 Audit)

### Pitfall 1: `localhost` for remote services

**Symptom:** Registry says `host: localhost` but service runs on another asset.

**Reality:** Service is on `192.168.1.54`, but YAML says `localhost`.

**Fix:** Replace `localhost` with the actual IP from `runs_on` asset.

### Pitfall 2: Multiple services same port

**Symptom:** phpmyadmin and open-webui both say port `8080` on same host.

**Reality:** Only one can actually listen on that port. Investigation reveals:
- OpenWebUI: 8080
- phpMyAdmin: 80 (Apache)

**Fix:** Verify with curl, update the incorrect one.

### Pitfall 3: Container port exposure vs host listening

**Symptom:** Registry has port from container's internal config, not host exposure.

**Example:** AdGuard Home container listens on 8083 internally, but is that exposed?

**Fix:** Check `docker ps` port mappings AND `ss -tlnp` on host. Use the host-listening port.

### Pitfall 4: Services that won't respond to curl

**Symptom:** Port is listening (ss shows it) but curl returns nothing.

**Causes:**
- Non-HTTP protocol (DNS on 53, MySQL on 3306)
- Service requires specific protocol handshake

**Fix:** Use protocol-appropriate probe:
```bash
# DNS
dig @localhost google.com +short

# MySQL
mysql -h localhost -u test -e 'SELECT 1' 2>&1 | head -1

# Raw TCP
echo '' | timeout 2 nc localhost <port> && echo 'Port open' || echo 'Closed'
```

### Pitfall 5: Stopped containers with stale Registry data

**Symptom:** Registry says `status: operational` but `docker ps` shows `Exited`.

**Fix:** Update YAML: `status: stopped` and remove or comment out network section.

## Reference Commands Cheat Sheet

```bash
# SSH + port scan
ssh user@host "ss -tlnp | grep -E ':(3000|8080|80|443) '"

# SSH + curl identification
ssh user@host "for p in 80 3000 8080 8888; do echo \"Port \$p:\"; curl -s --max-time 2 http://localhost:\$p 2>&1 | grep -o '<title>[^<]*</title>' || echo 'No HTTP'; done"

# Docker port inspection
ssh user@host "docker inspect --format '{{.Name}}: {{.NetworkSettings.Ports}}' \$(docker ps -aq)"

# Background process check (non-Docker)
ssh user@host "ps aux | grep -E 'python|java|node|hermes' | grep -v grep"
```

## Jun 2026 Audit Results (CIC Registry)

**Scope:** 17 software entities across 4 assets

**Findings:**
| Service | Old Host | New Host | Old Port | New Port | Evidence |
|---------|----------|----------|----------|----------|----------|
| hermes | 192.168.1.54 | 192.168.1.52 | 8000 | 8000 | ps aux on .52 |
| phpmyadmin | 192.168.1.54 | 192.168.1.54 | 8080 | 80 | curl port 80 → phpMyAdmin title |
| adguardhome | 192.168.1.54 | 192.168.1.54 | 3000 | [8083, 53] | AdGuardHome.yaml config |
| unbound | 192.168.1.54 | 192.168.1.54 | 53 | 53 | operational→stopped (config errors) |
| portainer | 192.168.1.54 | 192.168.1.54 | 9000 | 9443 | ss -tlnp confirmed 9443 |
| mysql | localhost | 192.168.1.54 | 3306 | 3306 | ss confirmed |
| ollama | localhost | 192.168.1.54 | 11434 | 11434 | curl confirmed |
| metabase | localhost | 192.168.1.54 | 3000 | 3000 | curl confirmed |
| open-webui | localhost | 192.168.1.54 | 8080 | 8080 | curl confirmed |
| searxng | localhost | 192.168.1.54 | 8888 | 8888 | curl confirmed |

**Total YAMLs modified:** 12

**Lesson:** Never trust `localhost` or remembered ports. Always verify with SSH + ss/curl before assuming network access patterns.