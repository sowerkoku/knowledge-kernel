---
name: registry
description: "Dual-graph resolver + indexed entity store. 6 functions: get, list, search, dependencies, dependents, validate."
version: 1.12.0
validated: true
---

# Registry Skill

## Objetivo

Indexa YAMLs en `/home/carlos/registry/` y expone 6 funciones para consultarlos. Solo lectura.

## Ubicación

```
~/.hermes/skills/registry/
├── SKILL.md          # este archivo — API reference minima
├── registry/
│   ├── __init__.py
│   ├── indexer.py   # RegistryIndex — grafo en memoria
│   └── query.py      # 6 funciones publicas
├── docs/             # narrativa — patrones, auditoria, errores
├── references/       # archivos de referencia tematica
├── scripts/          # network_report.py, verify_*.py
└── tests/
    └── test_registry.py
```

Narrativa extensa: ver `docs/`. Estado actual del Registry: `git log` en `/home/carlos/registry/`.

## API — 6 Funciones

### registry_get(id) → dict | None
Entidad completa por ID. `None` si no existe.

### registry_list(category=None) → list[dict]
Lista entidades. `category` = `assets | software | data | automation | projects | procedures | endpoints`. `ValueError` si categoría inválida.

### registry_search(query) → list[dict]
Búsqueda case-insensitive en id, name, description, tags. Retorna `{id, name, category, match_field, score}` ordenado por score desc.

### registry_dependencies(id, recursive=False) → dict
```python
{
    "functional": [{"id": str, "status": str, "type": str, "criticality": dict}, ...],
    "infrastructure": [{"id": str, "status": str, "type": str, "criticality": dict}, ...]
}
```
`KeyError` si ID no existe.

### registry_dependents(id, recursive=False) → dict
```python
{
    "functional": [{"id": str, "status": str, "type": str, "criticality": dict}, ...],
    "infrastructure": [{"id": str, "status": str, "type": str, "criticality": dict}, ...]
}
```
- Si `id` es asset: `infrastructure` = qué corre en ese asset
- Si `id` es no-asset: `infrastructure` = entities en mismo host

`KeyError` si ID no existe.

### registry_validate() → dict
```python
{"valid": bool, "errors": [...], "warnings": [...],
 "stats": {"total": int, "by_category": dict}}
```

## Contrato de Semánticas — LOCK v1.0

```
depends_on  = grafo dirigido  (BFS transitivo,  recursive=True)
runs_on     = índice 1-hop    (NUNCA transitivo)
part_of     = grupo            (NUNCA se sigue)
```

| Concepto | BFS? | Transitivo? |
|---|---|---|
| depends_on | SÍ | SÍ |
| runs_on | NO | NO |
| part_of | NO | NO |

**Regla:** `sorted(set(...))` en toda lista retornada.

**Infrastructure lookup** usa tipo de entidad:
- asset → reverse lookup de runs_on
- no-asset → co-location via runs_on forward

## Uso

```python
from registry import (
    registry_get, registry_list, registry_search,
    registry_dependencies, registry_dependents, registry_validate,
)

# Por ID
e = registry_get("mysql")

# Por categoría
software = registry_list("software")

# Buscar
results = registry_search("hermes")

# Dependencias (transitivo)
deps = registry_dependencies("sync-firebird-mysql", recursive=True)
for e in deps["functional"]:
    print(f"  {e['id']}: {e.get('criticality',{}).get('business')}")

# Impacto (quién depende de X + su estado)
impact = registry_dependents("mysql", recursive=True)
for e in impact["functional"]:
    print(f"  {e['id']}: {e['status']} / {e.get('criticality',{}).get('business')}")

# Validar
v = registry_validate()
assert v["valid"], v["errors"]
```

## Categorías y sus entidades tipo

```
assets/         → servidores, pcs, dispositivos, routers
software/       → Docker containers, daemons, CLIs
data/           → databases, backups, datasets
automation/     → sync scripts, cron jobs
projects/       → proyectos CIC
procedures/     → runbooks, procesos documentados
endpoints/      → URLs/HTTP interfaces de software
```

##不走之法 (Anti-patterns)

- **No asumir localhost** — siempre consultar `network.host` del asset en `runs_on`
- **No mezclar runs_on con depends_on** — el primero es ubicación, el segundo es lógica
- **No seguir part_of en grafos** — es grupo, no dependencia
- **No hardcodear IPs** — consultar el Registry
- **No信任 YAML sin verificar** — `registry_validate()` antes de confiar

## Referencias

- `docs/usage-patterns.md` — patrones de diagnóstico y consulta
- `docs/audit-methodology.md` — auditoría en 9 niveles
- `docs/error-log.md` — errores comunes detectados (single source)
- `docs/governance.md` — Regla 0, evolución, gobernanza
- `references/` — archivos temáticos (dns-fingerprinting, lock-contract, etc.)