# LOCK v1.0 — Contrato de Relaciones en CMDB/registry

> Aplicar SIEMPRE al modelar entidades en `registry@.52` o `cmdb@.53`.
> Basado en errores reales cometidos y documentados en `registry@.52` (v1.0-v1.7).

## Las 3 relaciones — separación estricta

```yaml
depends_on:   Grafo DIRIGIDO (transitivo) — relación LÓGICA/RUNTIME
runs_on:      Índice de LOCALIZACIÓN (1-hop) — relación FÍSICA/HOST
part_of:      Etiqueta de GRUPO (sin traversal)
```

**Regla absoluta:** estos tres **NUNCA** se mezclan en un mismo traversal. Cada uno tiene su query.

---

## depends_on — Runtime/logical dependency

- **Tipo:** grafo dirigido
- **Transitivo:** SÍ (`recursive=True` expande con BFS)
- **`part_of`:** NUNCA se sigue
- **Terminals:** software/data/automation sin depends_on son nodos hoja

**Cuándo usar:** cuando una cosa **requiere** otra para funcionar lógicamente.
- MySQL requiere el motor MySQL `depends_on: [mysql]`
- sync_bridge CIC requiere las DBs `depends_on: [firebird-eleventa, mysql-db-raw]`
- contenedor docker requiere docker `depends_on: [docker]`

## runs_on — Localización física

- **Tipo:** attribute lookup (NO grafo)
- **Transitivo:** NUNCA — `runs_on` es siempre 1-hop
- **Operación:** co-location query / group by host

**Cuándo usar:** cuando una cosa **vive adentro de** un host físico.
- DB `runs_on: [orange-pi-54]`
- contenedor `runs_on: [orange-pi-54]`
- NO `runs_on: [mysql]` ← ERROR: DB existe dentro de MySQL, no corre en MySQL

## part_of — Membresía de grupo

- **Tipo:** etiqueta (sin traversal nunca)
- **Uso:** referencias lógicas a "este proyecto/sistema/entidad-de-negocio"
- **`part_of: [cic]`** indica "pertenece al CIC" pero NUNCA expande

---

## Directional Typing — `infrastructure` cambia según tipo

Cuando devolvés `dependents(id)['infrastructure']` el query cambia según categoría de la entidad consultada:

```python
if category == "assets":
    # "¿Qué corre en este asset?" → reverse lookup de runs_on
    infrastructure = reverse_runs_on_lookup(id)
else:
    # "¿Dónde corre este nodo?" → forward runs_on → inverse lookup
    infrastructure = resolve_co_location(id)
```

---

## Normalización — determinismo

**TODA lista de IDs retornada por cualquier op debe usar:**
```python
return sorted(set(internal_list))
```

Razón: el output debe ser determinista para que diff-comparaciones y tests no rompan.

---

## Errores típicos (los 5 más comunes)

### 1. DB con `runs_on: [mysql]`
**Mal:** DB corre en MySQL
**Bien:** MySQL es un motor, no un host. DB vive en un host.
```yaml
# Mal
id: db-cic
runs_on: [mysql]

# Bien  
id: mysql-db-cic
runs_on: [orange-pi-54]      # FÍSICO
depends_on: [mysql]          # RUNTIME
```

### 2. `firebird-eleventa` con `runs_on: [firebird]`
**Mal:** Firebird es el host
**Bien:** Firebird es software, no host
```yaml
# Bien
id: firebird-eleventa
runs_on: [servidor-pos]      # PC Windows
depends_on: [firebird-engine]
```

### 3. Contenedor con `runs_on: [docker]`
**Mal:** Container corre en docker
**Bien:** Container corre en host, DEPENDE de docker
```yaml
# Bien
id: metabase
runs_on: [orange-pi-54]
depends_on: [docker]
```

### 4. Mezclar impact funcional con co-ubicación en reporte
**Mal:** `total_afectados = functional + infrastructure` (suma dos cosas no sumables)
**Bien:** Reportar `functional: [...]` y `infrastructure: [...]` por separado

### 5. Asumir servicio local sin verificar red
**Mal:** `mysql -u root -e "SHOW DATABASES"` (asume localhost)
**Bien:** `registry_get('mysql-db-cic')` → `ping 192.168.1.54` → `nc -z 192.168.1.54 3306` → `mysql -h 192.168.1.54`

---

## Otros 9 errores documentados (resumen)

Ver `common-errors.md` para los 14 completos. Breve:

| # | Error |
|---|-------|
| 6 | `claim "backup.enabled=false" sin verificar realidad` |
| 7 | `concluir "es irrecuperable"` (mejor: "recuperabilidad no demostrada") |
| 8 | `mezclar audit de modelo con audit de realidad` |
| 9 | `medir cobertura preguntando al usuario` (usar evidencia: ping/systemctl/docker ps) |
| 10 | `git initialized ≠ gobernanza cerrada` |
| 11 | `usar cmdb antes de asumir IPs/ubicaciones` |
| 12 | `asumir NAS cuando es POS` (verificar tipo de cada asset) |
| 13 | `conflar categorías de recuperación` (R ≠ RT ≠ RC ≠ RP) |
| 14 | `saltarse verificar red antes de conectar` |

---

## Por qué este LOCK existe

Junio 2026: la confusión entre `runs_on` y `depends_on` generó inferencias falsas (hermes↔mysql parecía depender mutuamente cuando en realidad uno corre en el otro). Forzar la separación **al modelar** evita que cualquier query posterior devuelva basura.

**Es LOCK v1.0 porque no se cambia sin crisis real.** Modificar implica romper formats y tests en registry@.52 (32 entidades afectadas).
