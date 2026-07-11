# Audit Report — Registry → agent-cmdb (2026-07-06)

## Source: ~/registry → 85 entidades

## Resultado del audit dry-run

```
============================================================
REGISTRY AUDIT REPORT
============================================================

Total entities:     85
Auto-migratable:    85
Requires干预:        0
Skipped:            0

Acceptance readiness: 100%

Schema versions:
  v1 (legacy):    85
  v2 (current):   0

By domain:
  infrastructure  (Infraestructura):  40
  software        (Software       ):  40
  organization    (Organización   ):   5

By kind:
  agent...............   5
  asset...............  25
  automation..........   3
  endpoint............  13
  network.............   2
  software............  37

  Broken relations: 1
    - sshd: listens_on -> ip-[::]

------------------------------------------------------------
SUCCESS CRITERIA
------------------------------------------------------------
  ✅ 100% schema valid
  ✅ 0 duplicate IDs
  ❌ 0 broken relations   ← 1 relación rota: sshd → ip-[::]
  ✅ 0 unknown kinds

❌ NOT READY — 1 broken relation needs fix
```

## Issues identificados

### 1. Broken relation (1)

```yaml
# Entidad: sshd
# Relation: listens_on -> ip-[::]
# Problema: ip-[::] no es un entity ID válido
```

**Fix requerido:** Editar la entidad sshd para apuntar a un entity ID real o eliminar la relación.

### 2. Legacy schema (85/85 = 100%)

Todas las entidades usan schema_version: 1. Requieren migrate a schema v2 (domain+kind).

## Conclusión

**Acceptance readiness: 100%** — La única intervención necesaria es arreglar 1 relación rota. Una vez corregida, la migración está lista.

## Lesson learned

El audit tool reveló que la mayoría de los kinds legacy (hardware, configuration, data) necesitaban mapping en `DEPRECATED_KINDS` antes de que el audit pudiera procesarlos correctamente. Sin el audit, habríamos migrado entidades con kinds no reconocidos silenciosamente.