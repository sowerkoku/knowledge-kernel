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
agents/        → perfiles Hermes vivos (Devon, Arquitectobi, IngenieroSQL, etc.)
assets/        → servidores, pcs, dispositivos, routers
software/       → Docker containers, daemons, CLIs
data/           → databases, backups, datasets
automation/     → sync scripts, cron jobs
projects/       → proyectos CIC
procedures/     → runbooks, procesos documentados
endpoints/      → URLs/HTTP interfaces de software (placeholder)
```

## Principios Arquitectónicos de Skills (Cico)

> "La skill debe manejar solo hechos, la narrativa y docs deben vivir fuera (wiki u otro lugar). Versionado con git, historia con commits. La skill son hechos (.yaml indexables) nada que no sea indexable puede vivir en la skill." — Cico, 2026-06-22

### Estructura de una skill bien diseñada

```
skill/
├── SKILL.md          # SOLO hechos indexables: API, trigger, pitfalls, verification
│                      # NUNCA: estado actual, IPs, paths, narrativa extensa
├── docs/             # narrativa, patrones, guías de uso
├── references/       # conocimiento temático detallado
├── scripts/          # acciones re-ejecutables
└── tests/            # validación de invariantes
```

### Qué VA en SKILL.md
- API de funciones
- Trigger conditions
- Pitfalls documentados
- Verificación steps
- Anti-patterns
- Referencias a `docs/` (`docs/*.md`)

### Qué NO VA en SKILL.md
- IPs, paths, nombres de archivos específicos (envejecen)
- Estado actual del sistema (snapshot que envejece)
- Narrativa > 10 líneas
- Contenido no indexable

### Docs externos
Narrativa, patrones de uso, auditorías van en `docs/`. No compiten con el skill — lo complementan.

### Git para skills
Iniciar repo git en `~/.hermes/skills/<skill>/`. Cada cambio significativo = commit. Git guarda historia.

### GitHub: SSH ≠ API Token
- **SSH** (`git@github.com:...`): solo clone/push a repos que ya existen
- **API Token** (OAuth PAT): crear repos, issues, gestionar recursos
- Push a repo inexistente → `ERROR: Repository not found` — GitHub no auto-crea

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