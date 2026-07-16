# agent-cmdb Design Principles — Session 2026-07-07

Principios que emergieron de la sesión de revisión de API + integración con Hermes.

---

## 1. Separación de responsabilidades en la API

Cada función tiene un dominio claro. No mezclar:

| Función | Dominio |
|---|---|
| `cmdb_get()` | Describe la entidad |
| `cmdb_impact()` | Analiza consecuencias y dependencias |

**Anti-patrón:** usar `cmdb_impact()["i_depend_on"]` para responder "¿dónde corre X?"
porque mezcla análisis de impacto con consulta de entidad.

**Patrón correcto:** propiedad computada `entity.runs_on`.

---

## 2. Propiedades computadas para vistas derivadas

`runs_on` no está en `metadata`. Existe en `relations` (YAML). Se expone como propiedad computada.

Misma filosofía que `freshness`:
- No duplicar datos
- No cambiar el modelo
- Exponer vista conveniente calculada en acceso

```python
@property
def runs_on(self) -> Optional[str]:
    for rel in self.relations:
        if rel.get("type") == "runs_on":
            return rel.get("target")
    return None
```

**Regla:** antes de agregar un campo derivado a metadata, considerar propiedad computada en `Entity`.

---

## 3. Contrato de API: documentar tipo exacto, no solo nombre

Cada miembro de la API debe documentarse con:
- Tipo (Property / Method / str / dict / etc.)
- Qué retorna exactamente
- Si es enum, nombrar los valores posibles

**Errores evitados en esta sesión:**
- `is_fresh` es método, no propiedad → `r.evidence.is_fresh()`
- `time_to_expiry_seconds` es método → `r.evidence.time_to_expiry_seconds()`
- `confidence_level` es enum `ConfidenceLevel` → `r.evidence.confidence_level.value`
- `confidence_basis` es `list[EvidenceBasis]` → `r.evidence.confidence_basis[0].value`

---

## 4. `expires_at` es contrato público — no eliminar aunque sea computado

`evidence.expires_at` forma parte de la API pública. Aunque se compute de `observed_at + ttl`, no debe eliminarse ni substituirse por una fórmula — los consumidores ya la consultan.

**Regla:** una vez publicado en la API, mantener la propiedad aunque internamente sea derivada.

---

## 5. FGR: medición sintética ≠ medición operacional

Un acceptance test con consultas conocidas даёт FGR = 100%. Eso valida la integración — no mide adopción real.

**Medición operacional requiere:**
- Cuántas conversaciones reales invocaron el Kernel
- Cuántos hechos pidió el agente vs cuántos encontró
- Cuántas afirmaciones del LLM estaban respaldadas por hechos del Kernel

**No medir FGR con cron jobs de preguntas fijas.** Instrumentar Hermes para registrar uso real.

---

## 6. El rol de agent-cmdb: grounding, no infraestructura

Frase que captura el rol:

> "agent-cmdb no es infraestructura para el LLM; es infraestructura para el grounding del LLM."

El objetivo no es que el modelo responda más preguntas, sino proporcionar una base factual determinista para que el razonamiento posterior tenga un punto de apoyo confiable.

---

## 7. runs_on: la relación está en YAML, no en metadata

**Dato verificado empíricamente:**
```
ollama.yaml:
  relations: [{type: runs_on, target: app-server-01}]

cmdb_get('ollama').entity.metadata  → {name, description}  (SIN runs_on)
cmdb_get('ollama').entity.runs_on   → "app-server-01"       ✅ (computed)
```

Esto NO es un bug — es el diseño funcionando. La relación existe en `relations` y se expone via propiedad computada.

---

## 8. Compatibilidad: Core Tests deben pasar 100% antes de release

Los 14 Core Tests verifican que el sistema funciona, no que existen datos específicos. Son la línea antes de cualquier push.

```
cd ~/agent-cmdb
CMDB_DATA_DIR=~/knowledge/agent-cmdb \
  ~/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/test_acceptance.py -v -k "Core"
```