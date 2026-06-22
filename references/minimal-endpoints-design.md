# Endpoints: Minimalist Design (Anti-Duplication Pattern)

**Fecha:** 2026-06-21  
**Episodio:** Majoral (refactor) — endpoints were initially created with duplicated `name`, `description`, `relations` fields from software/

---

## El problema: duplicación de información

Cuando se crearon los primeros endpoints, el patrón inicial incluyó campos que YA existían en `software/`:

```yaml
# ❌ DUPLICADO — name, description, relations ya viven en software/metabase.yaml
id: metabase-ui
category: endpoints
type: bi-dashboard
name: Metabase                    # duplicado de software/
description: Tableros B.I...       # duplicado de software/
relations:
  part_of: [cic]                  # duplicado de software/
url: http://192.168.1.54:3000
service_ref: metabase
```

**Problemas con duplicación:**
- Si cambia `name` de `metabase` en software/, toca actualizar 2 archivos
- Mantenimiento en dos fuentes = drift eventual
- Viola el principio Registry: TYPE B (configmutable) sale del Registry

---

## El patrón correcto: endpoints minimalistas

Un endpoint SOLO debe tener lo que es **único** del punto de acceso:

```yaml
# ✅ MINIMALISTA — solo campos propios del endpoint
id: metabase-ui
category: endpoints
type: bi-dashboard
name: Metabase                    # ← único campo "humano" necesario (para list())
url: http://192.168.1.54:3000    # ← único: URL completa (software solo tiene host+port)
service_ref: metabase             # ← vínculo al software (no duplica nada)
access: internal                  # ← único: nivel de acceso
auth: required                    # ← único: requerimiento de auth
notes: Credenciales en secrets/metabase.yaml
```

**Lo que NO va en un endpoint:**
- `description` → ya está en software/
- `relations` → ya están en software/
- `network.host`, `network.port` → ya están en software/
- `status` → ya está en software/

**Lo que SÍ va:**
- `url` → la diferencia clave (URL completa, no host+port separados)
- `service_ref` → vínculo al software que lo provee
- `access` → public | internal | localhost (nivel de acceso de red)
- `auth` → required | none | token (requerimiento de autenticación)
- `notes` → info operativa adicional

---

## El campo `name` en endpoints

El campo `name` en endpoints ES necesitado por `registry_list()` que construye resúmenes con `entity["name"]`. Pero el nombre del endpoint PUEDE diferir del software:

| software/ name | endpoint/ name | Por qué |
|----------------|----------------|---------|
| Metabase | Metabase | Mismo nombre |
| Ollama | Ollama API | El endpoint es la API, no la UI |
| AdGuard Home | AdGuard DNS | Dos endpoints (UI y DNS) para mismo software |

**Regla:** El `name` del endpoint es para legibilidad humana. Puede ser igual o diferente al software. Mínimo 3 caracteres.

---

## Validación del indexer para endpoints

El validador genera warnings "Entidad sin relaciones definidas" porque espera un bloque `relations`. Para endpoints, la relación es `service_ref`. El indexer debe excluir endpoints de esta regla:

```python
# indexer.py — línea ~341
if not has_relation and entity.get("category") != "projects" and entity.get("category") != "endpoints":
    warnings.append({"file": ..., "warning": "Entidad sin relaciones definidas"})
```

Sin este ajuste, todo endpoint minimalista genera un warning falso.

---

## Costo de mantenimiento: service_ref como única fuente de verdad

Cuando cambia el `name` o `description` del software, el endpoint NO necesita actualización — la información completa vive en software/.

El único mantenimiento necesario en endpoints es cuando:
- La URL cambia (ej: puerto 9000 → 9443)
- El nivel de acceso cambia (internal → public)
- El requerimiento de auth cambia (none → required)
- El software se mueve a otro host

**No maintenance cuando:**
- El software cambia de descripción
- El software cambia de relaciones
- El software cambia de status

---

## Template rápido para nuevo endpoint

```yaml
id: <service>-<tipo>
category: endpoints
type: <web-ui|api|dns-server|agent-gateway|container-ui|db-ui|bi-dashboard|llm-ui|llm-api|search-ui|dns-ui>
name: <nombre legible>
url: <url completa>
service_ref: <id-del-software>
access: internal|localhost|public
auth: required|none
notes: <opcional>
```

**Verificación post-creación:**
```python
from registry.query import registry_validate
v = registry_validate()
# Debe dar: VALID: True, Warnings: 0
```