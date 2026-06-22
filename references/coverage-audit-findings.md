# Coverage Audit Findings — 2026-06-12 (Actualizado)

## Resumen Ejecutivo

El Registry modela aproximadamente **80-90% de la realidad operativa del CIC** (post-limpieza de items históricos).

Los mayores vacíos fueron resueltos:
- sync_CICO → Histórico (sync_bridge es la versión operativa)
- OpenClaw → Exagente, no operativo
- Firebird backup real documentado

---

## Elementos Clarificados por el Usuario

| Elemento | Antes | Después |
|---|---|---|
| sync_CICO | ¿Activo? | **Histórico** — sync_bridge es la versión operativa |
| OpenClaw | ¿Modelar? | **Descartado** — exagente, no operativo |
| Hermes profiles | ¿Modelarlos? | **Descartado** — perfiles de trabajo, no entidades |
| firebird-eleventa backup | `enabled: false` (incorrecto) | **Corregido** — backup manual en PC(.2) + PC personal |

---

## Cobertura Estimada (Post-Limpieza)

| Categoría | Antes | Después |
|---|---|---|
| Automatización | ~40% | ~80% (sync_CICO descartado) |
| Software | ~70% | ~90% (OpenClaw descartado) |
| Backups reales | ~30% | ~80% (firebird documentado) |
| **Global** | **~50-60%** | **~80-90%** |