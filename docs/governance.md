# Gobernanza — Registry Skill

Reglas de evolución y mantenimiento. Separación Registry ≠ Wiki/ADR.

---

## Regla 0 (CRÍTICA)

> **No se modifica la estructura del Registry hasta que una consulta real falle.**

Esto significa:
- No agregar categorías por anticipación
- No agregar campos por anticipación
- No agregar bases de datos por anticipación
- No agregar grafos por anticipación

**Primero aparece una pregunta que el Registry no puede responder. Luego se determina por qué. Luego se amplía.**

---

## Separación Registry ≠ Wiki/ADR

**El Registry responde:**
- ¿Qué existe?
- ¿Dónde está?
- ¿Qué depende de qué?
- ¿Cómo se accede?
- ¿Qué impacto tiene?
- ¿Es recuperable?

**El Registry NO responde:**
- ¿Por qué se decidió X?
- ¿Qué alternativas se evaluaron?
- ¿Quién tomó la decisión?
- ¿Qué cambió desde entonces?

El Wiki/ADR documenta el "por qué" — ver `/home/carlos/proyectos/cic-v3/docs/decisions/decision_log.md`.

---

## La Pregunta Estratégica

> Si mañana desaparezco por una semana, ¿alguien podría operar el CIC usando solamente Registry + Runbooks?

Esta pregunta determina qué gaps son realmente críticos y cuáles son mejoras opcionales.

---

## Evolución por Decisiones de Diseño

El Registry evoluciona por gaps acumulados con impacto de decisión, no por intuición del agente.

**Criterio:** Impacto de decisión, no frecuencia. Una pregunta que aparece una vez al año pero bloquea una decisión crítica justifica modelado.

**Gaps no respondibles se registran en:** `/home/carlos/proyectos/cic-v3/docs/decisions/decision_log.md`

---

## Campo criticality — Estándar

```yaml
criticality:
  business: critical|high|medium|low    # Impacto en negocio/ingresos
  operational: critical|high|medium|low # Impacto en operaciones diarias
  technical: critical|high|medium|low   # Complejidad/fragilidad técnica
```

**Definiciones:**
- `critical`: Sin esto, el negocio opera en modo crisis
- `high`: Degradación significativa pero manejable
- `medium`: Molestia operativa, workaround disponible
- `low`: Impacto mínimo, diferenciador no esencial

---

## Decisiones de diseño — Historial

Ver `/home/carlos/proyectos/cic-v3/docs/decisions/decision_log.md` para el registro completo de decisiones.

| Fecha | Decisión | Motivo |
|---|---|---|
| v1.0 | Separar `depends_on` (BFS) de `runs_on` (1-hop) | Evitar inferencias falsas |
| v1.0 | Normalización: `sorted(set(...))` | Determinismo del output |
| v1.7 | Registry ≠ Wiki/ADR — separación responsabilidades | Registry estado, Wiki historia |
| v1.8 | `network.host` = IP del asset en `runs_on` | localhost incorrecto en 12 YAMLs |
| v1.9 | DNS fingerprinting para identificación de devices | 9 devices descubiertos sin SSH |
| v1.12 | SKILL.md mínimo, docs externos | Facts indexables ≠ narrativa |

---

## Scripts de Auditoría

```bash
# Validar Registry
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_validate
v = registry_validate()
print(f'Valid: {v[\"valid\"]} — {v[\"stats\"][\"total\"]} entidades')
if v['errors']: print('ERRORS:', v['errors'])
if v['warnings']: print(f'Warnings: {len(v[\"warnings\"])}')"

# Ping sweep hosts
for ip in 192.168.1.{2,52,53,54,60,77}; do
    timeout 2 ping -c 1 -W 1 $ip 2>/dev/null | grep "from" \
        && echo "  $ip UP" || echo "  $ip DOWN"
done

# Puerto check
for port in 22 80 3000 3306 8080 8888 9443; do
    timeout 1 bash -c "echo >/dev/tcp/192.168.1.54/$port" 2>/dev/null \
        && echo "$port OPEN" || true
done

# Network report
cd ~/.hermes/skills/registry && python3 scripts/network_report.py --check
```