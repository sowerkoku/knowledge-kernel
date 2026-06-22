# Skill Registry

Dual-graph resolver + indexed entity store para el ecosistema CIC.

## Instalar

```bash
export PYTHONPATH="$PYTHONPATH:$HOME/.hermes/skills/registry"
```

## API

```python
from registry import (
    registry_get,       # detalle 1 entidad
    registry_list,     # listar por categoría
    registry_search,    # búsqueda full-text
    registry_dependencies,   # ¿De qué depende X?
    registry_dependents,     # ¿Quién depende de X?
    registry_validate,  # validar integridad
)
```

## Categorías

```
agents/       → perfiles Hermes vivos
assets/       → servidores, pcs, dispositivos
software/     → Docker containers, daemons
data/         → databases, backups
automation/   → sync scripts, cron jobs
projects/     → proyectos CIC
procedures/   → runbooks, procesos
endpoints/    → URLs/HTTP interfaces
```

## Tests

```bash
cd ~/.hermes/skills/registry
python3 tests/test_registry.py
```

## Docs

- `docs/audit-methodology.md` — 9 niveles de auditoría
- `docs/error-log.md` — errores comunes
- `docs/governance.md` — Regla 0, separación Registry/Wiki
- `docs/usage-patterns.md` — patrones de diagnóstico

## Principios

> "La skill debe manejar solo hechos, la narrativa y docs deben vivir fuera. Versionado con git. La skill son hechos (.yaml indexables) — nada que no sea indexable puede vivir en la skill." — Cico 2026-06-22

## Versionado

```bash
git log --oneline
```