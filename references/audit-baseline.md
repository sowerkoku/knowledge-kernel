# Registry Baseline — Respuestas Verificadas

Este documento contiene las respuestas **verificadas como correctas** del Registry.
Se usa para validar que el modelo responde correctamente antes de hacer impact analysis.

## Preguntas de Verificación (Level 2)

### 1. ¿Qué necesita Open WebUI para funcionar?

```python
deps = registry_dependencies('open-webui', recursive=False)
# needs (depends_on): ['docker', 'ollama']
# runs_on: ['orange-pi-54']
```

### 2. ¿Qué necesita Metabase para funcionar?

```python
deps = registry_dependencies('metabase', recursive=False)
# needs (depends_on): ['docker', 'mysql']
# runs_on: ['orange-pi-54']
```

### 3. ¿Qué necesita sync-firebird-mysql para funcionar?

```python
deps = registry_dependencies('sync-firebird-mysql', recursive=False)
# needs (depends_on): ['firebird', 'mysql']
# runs_on: ['orange-pi-54']
```

### 4. ¿Qué depende de Docker? (dependientes funcionales)

```python
deps = registry_dependents('docker', recursive=True)
# Dependientes funcionales: ['adguardhome', 'chromadb', 'crawl4ai', 'docmost', 'kanboard', 'metabase', 'open-webui', 'phpmyadmin', 'portainer', 'searxng', 'unbound']
# Infraestructura (co-hosting): todos los servicios en orange-pi-54 (no incluye docker mismo)
```

### 5. Si Firebird desaparece, ¿quién se afecta?

```python
deps = registry_dependents('firebird', recursive=True)
# Afectados: ['firebird-eleventa', 'sync-firebird-mysql']
# (firebird-eleventa corre en servidor-pos, sync-firebird-mysql depende de firebird)
```

## Modelo Semántico (correcto)

```
runs_on  = host físico (asset donde corre el proceso)
depends_on = dependencia lógica (runtime, servicio, base de datos que necesita)
```

### Ejemplos correctos:

| Entidad | runs_on | depends_on |
|---|---|---|
| open-webui | [orange-pi-54] | [docker, ollama] |
| metabase | [orange-pi-54] | [docker, mysql] |
| sync-firebird-mysql | [orange-pi-54] | [firebird, mysql] |
| mysql-db-raw | [orange-pi-54] | [mysql] |

### Errores de modelado corregidos:

- ❌ `runs_on: [docker]` → ✅ `depends_on: [docker]` (contenedor corre en host, no en docker)
- ❌ `runs_on: [mysql]` → ✅ `runs_on: [orange-pi-54], depends_on: [mysql]` (DB existe dentro de MySQL)
- ❌ `runs_on: [firebird]` → ✅ `runs_on: [servidor-pos]` (Firebird es software, no host)

## Validación

```bash
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_validate, registry_dependencies, registry_dependents

# 1. Registry válido
v = registry_validate()
assert v['valid'], f'Registry inválido: {v[\"errors\"]}'

# 2. Verificar las 3 preguntas críticas
checks = [
    ('open-webui', ['docker', 'ollama'], ['orange-pi-54']),
    ('metabase', ['docker', 'mysql'], ['orange-pi-54']),
    ('sync-firebird-mysql', ['firebird', 'mysql'], ['orange-pi-54']),
]

for entity_id, expected_needs, expected_runs in checks:
    deps = registry_dependencies(entity_id, recursive=False)
    needs = sorted(deps['functional'])
    runs = sorted(deps['infrastructure'])
    assert needs == expected_needs, f'{entity_id} needs: {needs} ≠ {expected_needs}'
    assert runs == expected_runs, f'{entity_id} runs: {runs} ≠ {expected_runs}'

print('✓ Registry válido y respuestas verificadas')
"
```

---

Última verificación: 2026-06-12
Registry version: 1.2.0