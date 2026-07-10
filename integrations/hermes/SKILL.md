---
name: knowledge-kernel
description: Knowledge Kernel — a deterministic grounding layer and shared source of truth for AI agents. Stores verified facts, evidence, relationships, and freshness. A shared source of truth that multiple agents can query before reasoning or acting.
category: infrastructure
version: 1.2.0
author: Carlos Cáceres
license: MIT
tags: [grounding, knowledge-kernel, deterministic-factual-substrate, facts, infrastructure, hallucination-prevention, endpoint-identity]
---

# knowledge-kernel Skill

**A Knowledge Kernel that provides deterministic grounding for AI agents.**

"LLMs infer; knowledge-kernel provides a shared, evidence-backed source of truth so multiple agents can reason from the same verifiable reality."

## Identidad

- **Identidad:** Knowledge Kernel (qué es)
- **Capabilidad:** Deterministic Grounding (qué aporta)
- **No es:** una CMDB, RAG, agent memory

## Contrato de Consumo

**Principio fundamental:**
- Si un hecho existe en el Kernel, prefiera el Kernel sobre inferencia.
- Si un hecho no está en el Kernel, trátelo como unverified.

Consulte el Kernel siempre que la pregunta involucre: infrastructure, software, endpoints, dependencies, agents, projects, policies, procedures, configuration facts.

**Anchored answers:** El Kernel puede aportar los hechos necesarios para que el agente ejecute tools adicionales (SQL, SSH, HTTP probes). Eso sigue siendo grounding.

## API

```python
from cmdb.api import (
    cmdb_exists,
    cmdb_get,
    cmdb_search,
    cmdb_list,
    cmdb_context,
    cmdb_impact,
    cmdb_assert,
    cmdb_validate,
)
```

Todo lo demás en el paquete `cmdb` es implementación interna.

## Configuración

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CMDB_DATA_DIR` | `~/.local/share/knowledge-kernel` | Directorio de entidades |
| `CMDB_CACHE_DIR` | `~/.cache/knowledge-kernel` | Directorio de cache |

## Version canónico

Este archivo es la versión shipping. La versión estándar con ejemplos completos y decision flow vive en `~/.hermes/skills/knowledge-kernel/SKILL.md`.

## Referencias

- Paquete `cmdb`: `~/agent-cmdb/cmdb/`
- Documentación: `~/agent-cmdb/README.md` y `docs/`