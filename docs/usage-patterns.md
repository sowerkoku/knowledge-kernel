# Usage Patterns — Registry Skill

Patrones de consulta validados. Narrativa operativa — el SKILL.md tiene la API mínima.

---

## Diagnóstico de Infraestructura Remota

**Orden obligatorio** al diagnosticar un servicio en una máquina remota:

```
1. registry_list('assets')       → Ver todas las máquinas disponibles
2. registry_get(asset_id)        → Obtener IP, puerto SSH, hostname
3. VERIFICAR RED (ping/puerto)    → Confirmar conectividad antes de asumir
4. registry_dependents(id)        → Entender qué depende de este servicio
5. CONECTAR al servicio real      → Solo después de verificar 1-4
```

**PITFALL CRÍTICO:** No asumir que el servicio está local. El Registry indica `runs_on: [asset_id]` — si el asset no es la máquina actual, verificar conectividad de red primero.

**MAL:**
```bash
mysql -u root -e "SHOW DATABASES"   # Fallo si MySQL está en 192.168.1.54
```

**BIEN:**
```bash
# 1. Obtener ubicación
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_get
mysql = registry_get('mysql')
print(f\"Host: {mysql['network']['host']}:{mysql['network']['port']}\")"

# 2. Verificar conectividad
ping -c 1 -W 2 192.168.1.54
for port in 22 3306; do
    timeout 2 bash -c "echo >/dev/tcp/192.168.1.54/$port" 2>/dev/null \
        && echo "Port $port: ABIERTO" || echo "Port $port: cerrado"
done

# 3. Solo entonces conectar
mysql -h 192.168.1.54 -u agente -p -e "SHOW DATABASES"
```

---

## Múltiples Instancias de un Servicio

Cuando un software corre en múltiples configuraciones (ej: Hermes con 5 profiles distintos), **cada instancia = entidad separada**:

```yaml
# hermes-arquitectobi.yaml
id: hermes-arquitectobi
category: software
config:
  profile: arquitectobi
network:
  host: 192.168.1.52
  port: 8000
```

**Reglas:**
1. Cada instancia = entidad separada con ID único desambiguado
2. Naming: `<nombre>-<config>` (ej: `hermes-arquitectobi`, NO `hermes-gateway-52`)
3. Campo `config.profile` o similar que identifique la variante
4. Evitar IDs genéricos que collapan múltiples instancias

**Validación:** `registry_validate()` debe pasar sin errores YAML.

---

## Análisis de Impacto antes de Apagar un Servicio

```bash
# ¿Qué se rompe si apago MySQL?
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_dependents
deps = registry_dependents('mysql', recursive=True)
print(f'Si MySQL cae, se afectan: {deps[\"functional\"]}')"
```

---

## Endpoints — Cuándo Usar la Categoría

`endpoints/` responde preguntas que `software/` solo NO puede:
- "¿Cuál es la URL completa de Metabase?" → `registry_get('metabase-ui').url`
- "¿Qué services usan el puerto 8080?" → search por `network.port`
- "¿Qué endpoints son públicos vs internos?" → `access: public|internal`
- "¿Qué endpoint requiere auth?" → `auth: required|none|token`

**Estructura endpoint:**
```yaml
id: metabase-ui
category: endpoints
url: http://192.168.1.54:3000
service_ref: metabase
access: internal
auth: none
```

**Regla de mantenimiento:** `endpoints/` duplica host+port del software — `service_ref` es el vínculo para actualizar coordinadamente. Ver `references/endpoints-schema.md`.

---

## Mapeo de Contenedores network=host

Containers con `--network=host` no aparecen en `docker ps --format "{{.Ports}}"`. Puertos reales en .54:

| Contenedor | Puerto | Verificado |
|---|---|---|
| metabase | :3000 | ss -tlnp + curl |
| open-webui | :8080 | ss -tlnp + curl |
| phpmyadmin | :80 | ss -tlnp (Apache) |
| adguardhome | :8083 | ss -tlnp |
| unbound | :53 | ss -tlnp |
| searxng | :8888 | docker ps (bridge) |
| portainer | :9443 | docker ps (bridge) |

**Comando para verificar:**
```bash
ssh carlos@192.168.1.54 'ss -tlnp | grep -E "LISTEN" | grep -v "127.0.0.54"'
```