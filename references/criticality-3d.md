# Criticality 3D — Business / Operational / Technical

> Aprendido de `registry@.52` v1.1. Reemplaza el modelo viejo de 4 niveles (critical/important/standard/low).
> **Regla:** "Análisis de impacto no puede depender de texto libre (tags, description)" — debe haber campos estructurados.

## Por qué 3 dimensiones independientes

Una sola etiqueta "critical" mezcla 3 cosas distintas:
- Impacto en negocio (¿se pierde plata?)
- Impacto operacional (¿se afecta la operatoria diaria?)
- Fragilidad técnica (¿es complejo/inestable?)

Un componente puede ser:
- `business: low` (`adguardhome` — no afecta ventas)
- `operational: medium` (afecta una capa de operación)
- `technical: high` (complejo, requiere cuidado)

Mezclar todo en "low" pierde la información para análisis de impacto.

## Las 4 sub-clases por dimensión

| Clase | Significado |
|-------|-------------|
| **critical** | Sin esto, el negocio opera en modo crisis |
| **high** | Degradación significativa pero manejable |
| **medium** | Molestia operativa, workaround disponible |
| **low** | Impacto mínimo, diferenciador no esencial |

## Definiciones (dominio-a-dominio)

### business

- **critical:** pérdida directa de ingresos / cierre del local
- **high:** pospone ventas, importa para SLA cliente
- **medium:** afecta eficiencia comercial
- **low:** no afecta ventas

### operational

- **critical:** bloquea el día operativo completo
- **high:** requiere workaround diario
- **medium:** requiere workaround trimestral
- **low:** afecta a muy pocos procesos

### technical

- **critical:** muy complejo, alto riesgo de cambio
- **high:** requiere cuidado per cambio
- **medium:** complejidad manejable
- **low:** cambio rutinario

## Esquema YAML

```yaml
criticality:
  business: critical    # Impacto en ingresos
  operational: critical # Operaciones diarias
  technical: medium     # Fragilidad/complejidad
```

## Tabla ejemplo CIC (referencia)

| Entidad | business | operational | technical | Por qué |
|---------|----------|-------------|-----------|---------|
| firebird-eleventa | critical | critical | high | POS — sin esto no se vende; reingreso manual complejo |
| mysql-db-cic | critical | critical | medium | flags + ventas; restore RT |
| orange-pi-54 | critical | critical | low | corre 2 DBs; reconstruir es copiar |
| mysql-db-raw | medium | high | medium | histórico; se puede regenerar parcial |
| hermes-agent | low | high | medium | agente — afecta capacidad de respuesta pero no ventas |
| metabase | medium | medium | high | BI — análisis se puede hacer manual |
| metabase BI | medium | medium | medium | impacto operativo, no crisis |
| docker | high | high | medium | runtime de 7 contenedores |
| adguardhome | low | low | low | DNS local, no bloquea ventas |
| portainer | low | medium | low | gestión docker — hay CLI |

## Cuándo usar cada dimensión

- **Análisis de impacto** (`registry_dependents` × `criticality`):
  - usar `business` para "¿qué pierdo si X cae?"
  - usar `operational` para "¿qué operación se bloquea?"
  - usar `technical` para "¿qué complejos resto si quiero recuperarlo?"

- **Filtrado SPOF** (`cmdb_critical`):
  - entity es SPOF si `business == critical` AND no hay redundancia con misma business.critical

## Anti-patrones

❌ "Esto es crítico" (sin dimensión) → no se puede comparar
❌ `criticality: critical` (string simple) → pierde análisis
❌ Mezclar las 3 en una sola etiqueta → análisis de impacto imposible
❌ Asumir "critical = SPOF" → puede haber redundancia

## Origen del cambio

Junio 2026 (`registry` v1.1): "Análisis de impacto no puede depender de texto libre (tags, description)". Migración de 4-tier → 3D fue forward-compatible; cualquier entity vieja con `criticality: critical` se interpreta como `business: critical` por default (con warning de validación).
