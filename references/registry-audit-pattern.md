# Registry Audit Pattern — 9 Fases Pre-Push

**Trigger:** Antes de hacer push del Registry a GitHub, o cuando hay dudas sobre la confiabilidad de los datos.

**Objetivo:** Validar que el Registry entrega información verificada y confiable.

---

## Fases de Auditoría

### Fase 1 — Baseline Tests (5 min)

```bash
cd ~/.hermes/skills/registry
python3 -c "
from registry import registry_validate
v = registry_validate()
print(f'Entidades: {v[\"stats\"][\"total\"]}')
print(f'Errores: {len(v[\"errors\"])}')
print(f'Warnings: {len(v[\"warnings\"])}')
if v['errors']:
    for e in v['errors']:
        print(f'  ERROR: {e[\"file\"]}: {e[\"error\"]}')
"
```

**Criterio PASS:** 0 errores, 0 warnings (o warnings menores aceptables).

**Fix típico:** Referencias a assets eliminados → limpiar `connects_to`, `depends_on`.

---

### Fase 2 — Audit YAMLs (10 min)

```bash
# Campos críticos en assets
python3 -c "
from registry import registry_list, registry_get
for a in registry_list('assets'):
    e = registry_get(a['id'])
    missing = []
    if not e.get('network', {}).get('ip'): missing.append('IP')
    if not e.get('status'): missing.append('status')
    if not e.get('criticality', {}).get('business'): missing.append('criticality.business')
    if missing:
        print(f'{a[\"id\"]}: {\", \".join(missing)}')
"
```

**Detectar MACs placeholder QEMU:**
```bash
python3 -c "
from registry import registry_list, registry_get
for a in registry_list('assets'):
    e = registry_get(a['id'])
    mac = e.get('network', {}).get('mac', '')
    if mac.startswith('52:54:00'):
        print(f'{a[\"id\"]}: MAC QEMU {mac}')
"
```

**Criterio PASS:** 0 campos críticos faltantes, 0 MACs QEMU.

---

### Fase 3 — Audit Funciones Core (15 min)

Tabla de pruebas mínimas:

| Función | Test | Esperado |
|---------|------|----------|
| `registry_get('mysql-db-cic')` | Tiene `network.host` | `192.168.1.54` |
| `registry_list('assets')` | Count | 16 assets |
| `registry_search('mysql')` | Resultados | 9 resultados |
| `registry_dependencies('metabase')` | Keys | `functional` + `infrastructure` |
| `registry_dependents('orange-pi-54')` | count | >0 servicios |

```bash
python3 -c "
from registry import registry_get, registry_list
# Test 1
mysql = registry_get('mysql-db-cic')
assert mysql.get('network', {}).get('host') == '192.168.1.54', 'mysql-db-cic sin host'
# Test 2
assert len(registry_list('assets')) == 16, 'asset count incorrecto'
# Test 3
assert len(registry_search('mysql')) > 0, 'search no encuentra mysql'
print('✅ Todos los tests core pasaron')
"
```

---

### Fase 4 — Audit Scripts (20 min)

```bash
cd /home/carlos/registry

# network_report.py funciona
python3 scripts/network_report.py --host orange-pi-54 | head -20
python3 scripts/network_report.py --host 54 | head -20  # numeric matching
python3 scripts/network_report.py --check  # ping sweep (<30s timeout)
```

**Criterio PASS:** `network_report.py` ejecuta sin errores, retorna datos coherentes.

**Note:** `verify_ports.py` y `verify_assets.py` pueden no existir (doc drift no blocking).

---

### Fase 5 — Cross-Validation vs Realidad (20 min)

**Comparar Registry contra 3 fuentes externas:**

```bash
# 1. Docker containers corriendo
ssh carlos@192.168.1.54 'docker ps --format "{{.Names}}:{{.Ports}}"'

# 2. ARP table (MACs reales)
ip neigh | grep "192.168.1."

# 3. Ping sweep
for ip in 1 2 4 52 53 54 77 94 101 109 122 128 140 144 148; do
    timeout 1 ping -c1 192.168.1.$ip >/dev/null 2>&1 && echo ".$ip: UP" || echo ".$ip: DOWN"
done
```

**Fixes típicos:**
- MACs incorrectas → corregir con ARP real
- Assets eliminados referenciados → limpiar `connects_to`
- DBs sin `network.host/port` → agregar

---

### Fase 6 — Audit Semántico (LOCK v1.0) (15 min)

**Verificar invariantes:**

```bash
python3 -c "
from registry import registry_get, registry_list

# Software NO tiene runs_on a software
for s in registry_list('software'):
    e = registry_get(s['id'])
    runs_on = e.get('relations', {}).get('runs_on', [])
    for ref in runs_on:
        ref_e = registry_get(ref)
        if ref_e and ref_e.get('category') == 'software':
            print(f'VIOLACIÓN: {s[\"id\"]} tiene runs_on: [{ref}] (software, no asset)')

# Contenedores NO tienen runs_on: [docker]
docker_containers = ['metabase', 'open-webui', 'phpmyadmin', 'portainer']
for c in docker_containers:
    e = registry_get(c)
    if e and 'docker' in e.get('relations', {}).get('runs_on', []):
        print(f'VIOLACIÓN: {c} tiene runs_on: [docker]')

# DBs NO tienen runs_on: [mysql]
for d in registry_list('data'):
    e = registry_get(d['id'])
    if 'mysql' in e.get('relations', {}).get('runs_on', []):
        print(f'VIOLACIÓN: {d[\"id\"]} tiene runs_on: [mysql]')

print('✅ LOCK v1.0 audit completado')
"
```

**Criterio PASS:** 0 violaciones.

---

### Fase 7 — Documentation Cross-Check (10 min)

```bash
# Funciones en SKILL.md existen en query.py
cd ~/.hermes/skills/registry
grep "^def registry_" registry/query.py

# References existen
ls -la references/

# Scripts existen
ls -la scripts/
```

**Criterio PASS:** 6/6 funciones existen, references/scripts mencionados existen (doc drift menor aceptable).

---

### Fase 8 — Audit Determinismo (10 min)

```bash
python3 -c "
from registry import registry_list, registry_dependencies

# registry_list determinista
list1 = registry_list('assets')
list2 = registry_list('assets')
list3 = registry_list('assets')
assert list1 == list2 == list3, 'registry_list no es determinista'

# registry_dependencies determinista
dep1 = registry_dependencies('hermes', recursive=True)
dep2 = registry_dependencies('hermes', recursive=True)
assert dep1 == dep2, 'registry_dependencies no es determinista'

# Output ordenado
assets_ids = [a['id'] for a in registry_list('assets')]
assert assets_ids == sorted(assets_ids), 'assets no están ordenados'

print('✅ Determinismo verificado')
"
```

**Criterio PASS:** 100% determinista, output ordenado.

---

### Fase 9 — Reporte GO/NO-GO

**Criterios GO:**
- ✅ 0 errores de validación
- ✅ 6/6 funciones core operativas
- ✅ LOCK v1.0 sin violaciones
- ✅ Determinismo verificado
- ✅ MACs corregidas vs ARP real
- ✅ YAMLs con campos críticos completos

**Warnings no-blocking:**
- ⚠️ references desactualizados
- ⚠️ scripts mencionados que no existen
- ⚠️ documentation drift

**Decisión:** Si las 8 fases anteriores pasan (aunque sea con warnings no-blocking), el Registry está **GO PARA PUSH**.

---

## Fixes Aplicados Típicos

1. **router-cic.yaml:** `connects_to: [pc-oficina]` → `connects_to: [caja-adicional]` (`.60` eliminado)
2. **mysql-db-cic.yaml:** Agregar `network.host: 192.168.1.54`, `network.port: 3306`
3. **MACs corregidas:** `samsung-148`, `android-tiktok-144`, `xiaomi-101` → ARP real

---

## Push a GitHub

```bash
cd /home/carlos/registry
git add -A
git commit -m "Audit fixes YYYY-MM-DD: N correcciones post cross-validation"
git remote -v  # confirmar remote configurado

# Si falla por host key:
ssh-keyscan github.com >> ~/.ssh/known_hosts
git push origin main
```

---

## Checklist Rápida

- [ ] Fase 1: 0 errores
- [ ] Fase 2: 0 campos críticos faltantes
- [ ] Fase 3: 6/6 funciones testeadas
- [ ] Fase 4: `network_report.py` funcional
- [ ] Fase 5: MACs vs ARP verificadas
- [ ] Fase 6: 0 violaciones LOCK v1.0
- [ ] Fase 7: Docs vs código coinciden
- [ ] Fase 8: Determinismo verificado
- [ ] Fase 9: GO para push

**Tiempo total estimado:** 90-120 minutos (automatizable con scripts).