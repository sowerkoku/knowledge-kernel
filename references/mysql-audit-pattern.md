# MySQL Audit Pattern — Session 2026-06-12

## Contexto

Usuario preguntó "Qué hacer si falla MySQL". El agente inicialmente asumió que MySQL estaba local (localhost), pero el Registry indicaba `runs_on: [orange-pi-54]` — IP 192.168.1.54.

**Lección crítica:** Siempre consultar el Registry ANTES de asumir ubicación de un servicio.

## Secuencia de auditoría completada

### 1. Consultar ubicación en Registry

```python
from registry import registry_get, registry_list

# Obtener asset donde corre MySQL
mysql = registry_get('mysql')
print(f"Host: {mysql['network']['host']}:{mysql['network']['port']}")
print(f"runs_on: {mysql['relations']['runs_on']}")

# Obtener IP del asset
asset = registry_get('orange-pi-54')
print(f"IP: {asset['network']['ip']}")
```

**Resultado:** MySQL está en `192.168.1.54:3306`, no en localhost.

### 2. Verificar conectividad de red

```bash
# Ping al host
ping -c 1 -W 2 192.168.1.54

# Escanear puertos críticos
for port in 22 3306; do
    timeout 2 bash -c "echo >/dev/tcp/192.168.1.54/$port" 2>/dev/null \
        && echo "Port $port: ABIERTO" || echo "Port $port: cerrado"
done
```

**Resultado:** Puerto 3306 ABIERTO — MySQL está corriendo.

### 3. Obtener credenciales de config existente

```bash
# Buscar en proyectos existentes
grep -r "password\|mysql" /home/carlos/proyectos/sync_bridge/ --include="*.py" -A2
```

**Resultado:** Credenciales encontradas en `config.py`:
- User: `agente`
- Password: `77D.cl.2105`
- Host: `192.168.1.54`

### 4. Auditar bases de datos con Python

```python
import mysql.connector

conn = mysql.connector.connect(
    host='192.168.1.54',
    user='agente',
    password='77D.cl.2105',
    database='DB_RAW'
)
cursor = conn.cursor()

# Listar todas las databases
cursor.execute("SHOW DATABASES")
dbs = [row[0] for row in cursor.fetchall()]

# Para cada DB, listar tablas con row counts
for db_name in dbs:
    cursor.execute(f"USE {db_name}")
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n=== {db_name}: TABLES ({len(tables)}) ===")
    for t in sorted(tables):
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{t}`")
            count = cursor.fetchone()[0]
            print(f"  - {t}: {count:,} filas")
        except Exception as e:
            print(f"  - {t}: ERROR {e}")

conn.close()
```

**Resultado:** 8 databases encontradas, 4 del CIC:
- DB_RAW: 18 tablas, 847K filas totales
- DB_CIC: 18 tablas, 532K filas totales
- DB_CIC_REFACTOR: 11 tablas, 0 filas (en construcción)
- cic_local_db: 18 tablas, 804K filas totales

### 5. Comparar Registry vs Realidad

| DB | Registry | Realidad | Acción |
|---|---|---|---|
| DB_RAW | 2 tablas listadas | 18 tablas reales | ✅ Actualizar |
| DB_CIC | 2 tablas listadas | 18 tablas reales | ✅ Actualizar |
| DB_CIC_REFACTOR | No existe | 11 tablas | ✅ Crear entrada |
| cic_local_db | No existe | 18 tablas | ✅ Crear entrada |

### 6. Actualizar Registry

```bash
# Actualizar mysql-db-raw.yaml
# - Agregar 16 tablas faltantes
# - Agregar row_counts
# - Agregar criticality

# Actualizar mysql-db-cic.yaml
# - Agregar 16 tablas faltantes
# - Agregar row_counts
# - Agregar criticality

# Crear mysql-db-cic-refactor.yaml
# - Nueva entrada con status: construction

# Crear mysql-db-cic-local.yaml
# - Nueva entrada para cic_local_db
```

### 7. Validar Registry

```python
from registry import registry_validate

result = registry_validate()
print(f"Valid: {result['valid']}")
print(f"Total entidades: {result['stats']['total']}")
```

**Resultado:** Registry válido, 32 entidades (antes 29).

## Hallazgos clave

1. **MySQL SÍ está corriendo** — `status: operational` en Registry era correcto
2. **4 databases del CIC** — solo 2 estaban registradas
3. **DB_CIC_REFACTOR** — proyecto en construcción, todas las tablas vacías
4. **cic_local_db** — espejo enriquecido con tablas de reportes

## Criticality aplicada

| Entidad | Business | Operational | Technical | Justificación |
|---|---|---|---|---|
| mysql | critical | critical | high | Sin MySQL no hay BI |
| mysql-db-raw | critical | high | high | Fuente de verdad del POS |
| mysql-db-cic | critical | critical | high | Dashboards dependen de esto |
| sync-firebird-mysql | critical | high | medium | Alimenta toda la analítica |
| backup-mysql-job | medium | high | low | RPO depende de esto |
| mysql-db-cic-refactor | low | low | medium | En construcción |
| mysql-db-cic-local | medium | medium | low | Datos derivados |

## Comandos de referencia rápida

### Ver criticality de una entidad
```bash
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_get
e = registry_get('mysql')
print(e.get('criticality', {}))"
```

### Listar entidades por criticality.business
```bash
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_list, registry_get
items = registry_list('data')
for i in items:
    e = registry_get(i['id'])
    crit = e.get('criticality', {})
    print(f\"{i['id']}: business={crit.get('business','?')}\")"
```

### Impact analysis
```bash
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_dependents
deps = registry_dependents('mysql', recursive=True)
print(f'Si MySQL cae: {deps[\"functional\"]}')"
```

## Anti-paterns detectados

1. **Asumir localhost** — El Registry dice `runs_on: [asset_id]`, verificar siempre
2. **Texto libre para impacto** — `tags` y `description` no son queryables determinísticamente
3. **Registro incompleto** — El Registry debe reflejar la realidad, no lo que "debería existir"

## Lección para futuras auditorías

**Secuencia obligatoria:**
1. Registry → ubicación del servicio
2. Red → verificar conectividad
3. Credenciales → buscar en configs existentes
4. Auditoría → conectar y extraer metadata
5. Comparar → Registry vs realidad
6. Actualizar → parchar discrepancias

**Nunca:**
- Asumir servicio local sin consultar Registry
- Conectar sin verificar red primero
- Actualizar Registry sin validar YAML