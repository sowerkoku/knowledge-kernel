# Auditoría del Registry — 9 Niveles

Metodología de auditoría progresiva. El Registry se audita en niveles que dependen uno del anterior.

Estado actual: ver `git log` en `/home/carlos/registry/` para historial de cambios. Los KPIs de cobertura en este documento son snapshots al momento de la auditoría, no valores actuales.

---

## Nivel 1: Inventario

```bash
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_list, registry_get
for a in registry_list('assets'):
    e = registry_get(a['id'])
    n = e.get('network', {})
    print(f\"{a['id']}: {n.get('ip','N/A')} status={e.get('status')} role={e.get('role')}\")"
```

## Nivel 2: Dependencias

```bash
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_dependencies
for entity in ['open-webui', 'metabase', 'sync-firebird-mysql']:
    deps = registry_dependencies(entity, recursive=False)
    print(f'{entity}: needs={sorted(deps[\"functional\"])}, runs_on={sorted(deps[\"infrastructure\"])}')"
```

## Nivel 3: Impact Analysis

Combina dependents × criticality. ¿Qué se rompe si X falla?

## Nivel 4: Recuperación y Operación

```bash
# Runbooks existentes
for p in registry_list('procedures'):
    e = registry_get(p['id'])
    print(f'{p[\"id\"]}: {e.get(\"description\")}')

# Entidades critical sin backup
for cat in ['data', 'software']:
    for item in registry_list(cat):
        e = registry_get(item['id'])
        if e.get('criticality', {}).get('business') == 'critical':
            has_backup = e.get('backup', {}).get('enabled', False)
            if not has_backup:
                print(f'❌ {item[\"id\"]}: critical sin backup')
```

## Nivel 4.5: Recoverability

Clasificación de recuperación:
- **R** = Se reinstala (docker-compose, apt) — < 30 min
- **RT** = Se restaura desde backup — 30-60 min
- **RC** = Se reconstruye desde source — horas a días
- **RP** = Se reemplaza hardware — semanas

## Nivel 5: Gobernanza

```bash
cd /home/carlos/registry && git status
cd /home/carlos/registry && git remote -v
cd /home/carlos/registry && git log --oneline | head -10
```

Git inicializado ≠ gobernanza cerrada. Verificar: ¿Existe remote? ¿Commits disciplinados?

## Nivel 6: Restauración

```bash
# Backup existe?
ls -la /backup/mysql/*.sql.gz 2>/dev/null | tail -5
# ¿Restore probado alguna vez?
```

**"backup existe" ≠ "restore funciona"**

## Nivel 7: Verificación de Puertos

```bash
# Registry dice: registry_list('software') → network.host + network.port
# Realidad: ssh <host> 'ss -tlnp | grep LISTEN'
```

Metodología: Registry vs Realidad. No confiar en YAML sin evidencia.

## Nivel 8: Assets — IP/MAC/hostname

```bash
for ip in 192.168.1.{2,52,53,54,60,77}; do
    timeout 2 ping -c 1 -W 1 $ip 2>/dev/null | grep "from" \
        && echo "  $ip UP" || echo "  $ip DOWN"
done
```

RED FLAGS: MAC `52:54:00:...` (QEMU placeholder), status `operational` sin `verified_YYYY-MM-DD`.

## Nivel 9: DNS Fingerprinting (AdGuard Home)

```bash
ssh carlos@192.168.1.54 'docker exec adguardhome tail -1000 /opt/adguardhome/data/querylog.json' 2>/dev/null | python3 -c "
import json,sys
from collections import defaultdict
domains_by_ip = defaultdict(set)
for line in sys.stdin:
    try:
        entry = json.loads(line.strip())
        ip = entry.get('IP','')
        qh = entry.get('QH','')
        if ip and qh: domains_by_ip[ip].add(qh)
    except: pass
for ip,doms in sorted(domains_by_ip.items()):
    print(f'{ip}: {len(doms)} domains')
    for d in sorted(list(doms))[:5]: print(f'  - {d}')
"
```

**Dominios confirmados por device (junio 2026):**

| Device | Dominios clave | IP |
|---|---|---|
| Samsung Galaxy A71 | api.whatsapp.net, b-graph.facebook.com, api.revenuecat.com | .128 |
| Xiaomi Router | api.miwifi.com, NTP pool, baidu.com | .101 |
| Xiaomi Phone | api.ad.intl.xiaomi.com, spot-pa.googleapis.com | .140 |
| Android TikTok | analytics.us.tiktok.com, a.gdflpr.com | .144 |
| Smart TV | encrypted-tbn*.gstatic.com, discover-pa.googleapis.com | .148 |
| Windows PC | login.live.com, edgedl.me.gvt1.com, chrome.cloudflare-dns.com | .4 |
| Linux server (Hermes) | api.telegram.org, models.dev, www.schemastore.org | .52 |

**Limitaciones:**
- Devices con DNS externo (8.8.8.8) no aparecen en querylog
- Un device puede tener múltiples OS fingerprints (apps cruzadas)
- Puerto 5335 en .54 es localhost-only, servicio desconocido

**Router credentials:** `Support:Bk8nKiXs` en 192.168.1.1:80

---

## Cobertura KPIs (snapshot auditoría 2026-06-21)

| Categoría | Cobertura | Gap Principal |
|---|---|---|
| Assets (servidores) | ~95% | .60 down, status no actualizado |
| Software | ~70% | OpenClaw system no modelado |
| Automation | ~40% | sync_CICO fuera del Registry |
| Backups reales | ~30% | Firebird backups en PCs no documentados |
| Procedimientos | ~20% | Conocimiento en bitacora/ no formalizado |

**Lo que existe en realidad pero NO en Registry:**
- `sync_CICO` (carpeta + cron) — NO ESTÁ
- `sync_bridge_copia`, `sync_bridge_copia2` — NO ESTÁN
- Hermes profiles en .53 — PARCIAL (agents/ en .53, endpoints/ en .54)
- Firebird backup en PC(.2) y PC personal — NO ESTÁ

**Metodología:** Comparar evidencia observada contra Registry, NO preguntar memoria. Fuentes: ping, docker ps, systemctl, crontab, ps aux, find .git.