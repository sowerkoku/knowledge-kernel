# CIC Registry — Auditoría Completa 2026-06-12

## Niveles de Auditoría

| Nivel | Pregunta | Estado | Score |
|---|---|---|---|
| 1 | ¿Qué existe? | ✅ Completado | 100% |
| 2 | ¿Cómo se relaciona? | ✅ Validado (modelo corregido) | 100% |
| 3 | ¿Qué impacto tiene una falla? | ⚠️ Parcial (data flow no modelado) | 70% |
| 4 | ¿Qué hacemos cuando falla? | ⚠️ Gaps identificados | 40% |
| 4.5 | ¿Se puede recuperar? | ✅ Clasificado A/B/C/D | 80% |
| 5 | ¿Está gobernado? | ⚠️ Git iniciado, remote pendiente | 50% |
| 6 | ¿El restore funciona? | ⚠️ Backup≠Restore probado | 30% |
| Coverage | ¿Modelo refleja realidad? | ⚠️ ~50-60% coverage | 50% |

---

## Hallazgos Críticos

### Gap #1 (Estratégico): firebird-eleventa

- **Problema:** `backup.enabled: false` según modelo, PERO existían backups manuales en PC personal y PC(.2)
- **Impacto real:** Si falla el disco del POS, se pierden ventas
- **Recoverability:** RC — **"recuperabilidad no demostrada", NO "irrecuperable"**
- **Corrección:** El modelo subestimaba la capacidad real. La pregunta correcta es: ¿existen backups funcionales?
- **Acción:** Documentar backups existentes, verificar integridad, probar restore

### Gap #2: servidor-pos

- **Problema:** ssh_user=desconocido, sin acceso documentado
- **Impacto:** Si falla la caja, nadie sabe cómo reiniciarla
- **Recoverability:** RP (hardware = semanas de espera)
- **Acción:** Documentar credenciales de acceso

### Gap #3: orange-pi-54

- **Problema:** Sin disaster recovery plan documentado
- **Impacto:** 16/32 entidades dependen de él
- **Recoverability:** RC (disco nuevo + restore)
- **Acción:** Crear DR checklist reproducible

### Gap #4: Cobertura del Registry

- **Problema:** El Registry modela ~50-60% de la realidad operativa
- **Elementos fuera del modelo:**
  - sync_CICO (activo en crontab)
  - OpenClaw automation system
  - Hermes profiles adicionales (5 instancias, solo 2 modeladas)
  - Firebird backups reales en PCs (fuera del modelo)
  - Documentación en bitacora/docs (no formalizada)
- **Acción:** No expandir modelo — primero medir cobertura real contra evidencia

---

## Recoverability Clasification (R/RT/RC/RP)

```
R  = Se reinstala (docker-compose, apt install)
RT = Se restaura (desde backup)
RC = Se reconstruye (desde otro source)
RP = Se reemplaza (hardware purchase)
```

### Entidades business=critical

| Entidad | Clasificación | Backup | Tiempo | Acción |
|---|---|---|---|---|
| firebird-eleventa | RC | ❌ | ∞ | PRIORIDAD 1 |
| servidor-pos | RP | ❌ | semanas | Documentar acceso |
| orange-pi-54 | RC | ❌ | 2-4h | DR plan |
| mysql | RT | ⚠️ Service | 30-60min | Verificar backup |
| mysql-db-raw | RT | ✅ | 30min | — |
| mysql-db-cic | RT | ✅ | 30-60min | — |
| docker | R | N/A | 15min | — |
| metabase | R | N/A | 5min | — |

---

## Lo que NO necesita runbook

Estos sistemas son `docker-compose up -d` en < 5 minutos:

- metabase, portainer, open-webui, searxng, adguardhome, unbound, phpmyadmin
- hermes (reinstallable desde repo)
- sync-firebird-mysql (restart del script)

---

## Preguntas sin responder aún (Gap Log acumulado)

```
gap:
  - id: 1
    question: "¿Cómo recupero firebird-eleventa si el disco falla?"
    date: 2026-06-12
    reason: "backup.enabled=false según modelo, pero existían backups manuales"
    decision_impact: "Recuperabilidad no demostrada — verificar backups existentes"
    
  - id: 2
    question: "¿Quién tiene acceso SSH a servidor-pos?"
    date: 2026-06-12
    reason: "ssh_user=desconocido"
    decision_impact: "Si falla la caja, nadie sabe cómo reiniciarla"
    
  - id: 3
    question: "¿Cuál es el RTO aceptable para cada servicio?"
    date: 2026-06-12
    reason: "No existe SLA definido"
    decision_impact: "No hay priorización en incidente"
    
  - id: 4
    question: "¿Git del Registry tiene remote push?"
    date: 2026-06-12
    reason: "Git inicializado pero sin remote configurado"
    decision_impact: "Repo vive en el mismo disco que los datos — no hay backup externo"
    
  - id: 5
    question: "¿El restore de mysql-db-cic funciona?"
    date: 2026-06-12
    reason: "backup.enabled=true pero nunca se probó restore"
    decision_impact: "Backup sin verificación es仮定 (asunción), no evidencia"
    
  - id: 6
    question: "¿Cuánto conocimiento operativo del CIC vive fuera del Registry?"
    date: 2026-06-12
    reason: "Cobertura estimada ~50-60% según reconciliación con evidencia real"
    decision_impact: "El modelo no refleja la realidad completa"
```

---

## Validación del Modelo (post-auditoría)

### Correcciones finales del modelo

Después de la auditoría, el usuario aclaró:

- **sync_CICO** → **Histórico**. `sync_bridge` es la versión operativa.
- **OpenClaw** → **Exagente**, no operativo. Descartado del modelo.
- **Hermes profiles** (arquitectobi, ingenierosql, qaconsistencia, webon) → Son perfiles de trabajo, no entidades separadas. El registry tiene `hermes` y `hermes-gateway-52` que son suficientes.

### Git Remote: Estrategia de Supervivencia

El Registry está en `/home/carlos/registry/` con Git local. La pregunta estratégica no es "dónde hacer push" sino "qué riesgo mitigo":

| Nivel | Protección | Escenarios cubiertos |
|---|---|---|
| 1 | Git local únicamente | Errores de edición |
| 2 | Git remote en otro servidor de la red | Errores de edición + pérdida del equipo |
| 3 | Git remote fuera de la infraestructura | Errores + incendio/robo/falla eléctrica |

**Opción C (recomendada):** GitHub (offsite) + clone local en .54

```
.52 (Registry local)
    ↓ push
GitHub (fuera de la casa)
    ↓ pull/clone
.54 (copia local operativa)
```

- Costo: ~5 min configuración
- Resuelve: desastre físico de todos los equipos
- Mantiene: copia local funcional sin internet

---

## Siguiente Paso Válido

El Registry actual es suficiente para inventario y dependencias. El siguiente módulo que justifique evidencia operacional sería un **Business Flow Graph** que capture:

- source of truth (Firebird)
- data stores (DB_RAW, DB_CIC)
- data consumers (Metabase dashboards)
- pipeline dependencies (sync-firebird-mysql)

Pero **primero** resolver los gaps #1 y #2 (firebird-eleventa y servidor-pos).