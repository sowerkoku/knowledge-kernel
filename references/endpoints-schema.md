# Esquema de Categoría: endpoints/

** Versión:** 1.0  
**Fecha:** 2026-06-20  
**Estado:** Activo

---

## Propósito

La categoría `endpoints/` responde preguntas sobre **puntos de acceso web** que la categoría `software/` no puede responder eficientemente:

| Pregunta | `software/` | `endpoints/` |
|----------|-------------|--------------|
| ¿Qué servicios web hay disponibles? | ❌ Iterar + filtrar | ✅ `registry_list('endpoints')` |
| ¿Cuál es la URL completa de X? | ❌ Construir host+port | ✅ `registry_get('x-ui').url` |
| ¿Qué endpoint usa el puerto 8080? | ❌ Sin índice inverso | ✅ Search por `port: 8080` |
| ¿Qué endpoints son públicos vs internos? | ❌ No hay campo | ✅ `access: public|internal` |
| ¿Qué endpoints requieren autenticación? | ❌ No hay campo | ✅ `auth: required|none` |

---

## Schema de archivo endpoint

```yaml
id: <unique-id>
category: endpoints
type: <ui|api|database|other>
name: <nombre-legible>
description: <descripción-corta>

url: <protocolo>://<host>:<port>/<path>
service_ref: <id-del-software-que-lo-provee>

access: public|internal|localhost
auth: required|none|token|basic
auth_ref: <opcional: referencia a credencial en secrets/>

tags: [<tag1>, <tag2>]

relations:
  part_of: [<proyecto-opcional>]
```

---

## Campos obligatorios

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | string | ID único global | `metabase-ui` |
| `category` | string | Siempre `endpoints` | `endpoints` |
| `type` | enum | Tipo de endpoint | `ui`, `api`, `database` |
| `name` | string | Nombre legible | `Metabase` |
| `url` | string | URL completa | `http://192.168.1.54:3000` |
| `service_ref` | string | ID de software en `software/` | `metabase` |

---

## Campos opcionales

| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `description` | string | Descripción extensa | — |
| `access` | enum | `public` (internet), `internal` (LAN), `localhost` (127.0.0.1) | `internal` |
| `auth` | enum | `required`, `none`, `token`, `basic` | `none` |
| `auth_ref` | string | Referencia a `secrets/<id>.yaml` | — |
| `tags` | list | Tags para búsqueda | `[]` |
| `relations.part_of` | list | Proyectos a los que pertenece | `[]` |

---

## Convenciones de naming

### IDs
- **Formato:** `<software>-<tipo>` (ej: `metabase-ui`, `ollama-api`, `mysql-db`)
- **Cuál evitar:** `metabase`, `ollama` (colisiona con software/)

### Tipos (`type` field)
- `ui` — Interfaz web para humanos (Metabase, Portainer, Open WebUI)
- `api` — API REST/GraphQL para programas (Ollama, Hermes gateway)
- `database` — Endpoint de base de datos (MySQL, Firebird)
- `other` — Otros (SSH, FTP, etc.)

---

## Ejemplos

### UI web interna
```yaml
id: metabase-ui
category: endpoints
type: ui
name: Metabase
description: Dashboard de BI para análisis de ventas y márgenes

url: http://192.168.1.54:3000
service_ref: metabase

access: internal
auth: required
auth_ref: metabase-admin

tags: [bi, dashboard, analytics]

relations:
  part_of: [cic]
```

### API local
```yaml
id: ollama-api
category: endpoints
type: api
name: Ollama API
description: API de inferencia de modelos LLM

url: http://192.168.1.54:11434
service_ref: ollama

access: localhost
auth: none

tags: [llm, api, inference]
```

### Gateway multi-profile
```yaml
id: hermes-arquitectobi-gateway
category: endpoints
type: api
name: Hermes Gateway (arquitectobi)
description: Gateway HTTP para el profile arquitectobi

url: http://192.168.1.52:8000
service_ref: hermes-arquitectobi

access: internal
auth: none

tags: [hermes, gateway, api]
```

---

## Relación con `software/`

**Regla de oro:** `endpoints/` **no reemplaza** `software/` — lo complementa.

- `software/` → Qué existe, dónde corre, de qué depende, cómo se instala
- `endpoints/` → Cómo se accede (URL completa, access, auth)

**Mantenimiento coordinado:**
- Si cambia `network.host` o `network.port` en `software/` → actualizar `url` en `endpoints/` correspondiente
- El campo `service_ref` es el vínculo entre ambas categorías

---

## Preguntas de diseño

### ¿Endpoints para servicios detenidos?

**Decisión:** NO. Solo endpoints de servicios `status: operational`.

**Rationale:** Un endpoint para un servicio stopped es información obsoleta que genera confusión ("¿por qué no puedo acceder a X?").

### ¿Endpoints por defecto en `localhost`?

**Decisión:** NO. Usar la IP real del asset donde corre el servicio.

**Rationale:** `localhost` es ambiguo en entornos multi-host. Si el servicio corre en `.54`, la URL debe ser `http://192.168.1.54:PORT`.

### ¿Cuántos endpoints por software?

**Decisión:** Uno por punto de acceso distinto.

**Ejemplos:**
- AdGuard Home → 2 endpoints: `adguardhome-ui` (8083) + `adguardhome-dns` (53)
- Hermes default → 1 endpoint: `hermes-default-gateway` (8000)
- MySQL → 1 endpoint: `mysql-db` (3306)

---

## Validación

El indexer debe validar:
1. ✅ `service_ref` apunta a un ID existente en `software/`
2. ✅ `url` es una URL válida (protocolo + host + port)
3. ✅ `access` es uno de: `public`, `internal`, `localhost`
4. ✅ `auth` es uno de: `required`, `none`, `token`, `basic`

---

## Gobernanza

**Regla 0 (del Registry):** No agregar endpoints por anticipación. Solo cuando una consulta real lo requiera.

**Trigger para crear endpoint:**
- Alguien pregunta "¿cuál es la URL de X?"
- Un agente necesita hacer `curl` a un servicio y no tiene la URL completa
- Se necesita listar todos los servicios web disponibles

**Trigger para NO crear endpoint:**
- El servicio no tiene interfaz web/red (ej: script local)
- El servicio está `status: stopped` o `decommissioned`