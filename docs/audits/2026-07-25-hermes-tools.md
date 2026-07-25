# Tool inventory audit — integrations/hermes/

Scope: 11 tools in `integrations/hermes/tools/` probed against the
live dataset (`hash=157d23fa`, 53 entities, 51 relations).

The report is organised by **plane**, matching the Inspector /
Kernel / Dataset / Runtime separation already encoded in the
project. Each section lists *what was observed*, not what it means.

## Tool Health — ¿funciona el software?

Probing mode: each wrapper imported and called directly with valid
inputs derived from the dataset; each CLI script invoked with no
arguments (per their own `__main__` blocks).

### Wrappers (importable modules)

| Tool | Input | Output signature | Status |
|---|---|---|---|
| `cmdb_exists` | real `adguardhome-54` | `{exists: True, entity_id: ...}` | ✓ |
| `cmdb_exists` | `fictional-9999` | `{exists: False, entity_id: ...}` | ✓ |
| `cmdb_get` | real `adguardhome-54` | full `entity` dict w/ kind/status/metadata | ✓ |
| `cmdb_assert` | wrong kind (asset/s/w) | `{valid: False, ...}` | ✓ |
| `cmdb_assert` | correct kind+status   | `{valid: True, ...}` | ✓ |
| `cmdb_impact` | real `adguardhome-54` | target + i_depend_on + depends_on_me | ✓ |
| `cmdb_context` | nonexistent agent id  | graceful error dict (no exception) | ✓ |

### CLI scripts

| Tool | Exit | Output signature | Status |
|---|---|---|---|
| `cmdb_engine_info` | 0 | 53 entities, hash 157d23fa, indexes populated | ✓ |
| `cmdb_reload` | 0 | reloaded:true, ~815ms reload | ✓ |
| `cmdb_stats` | 0 | 53 entities, 51 relations, breakdown by kind | ✓ |
| `grounding_pilot` | 0 | 16 questions loaded from ~/.hermes/telemetry/grounding | ✓ |
| `kpi` | 0 | DQS=100%, FFR=100%, valid=True, 33 warnings | ✓ |
| `run_pilot` | 0 | PILOT SUMMARY printed, summary saved to JSON | ✓ |

All 11 tools responded. No import errors, no syntax errors, no
unhandled exceptions.

## Dataset Health — ¿qué calidad tiene el conocimiento?

These describe the **state of the dataset**, not defects in tools.

### Validation

- 33 validation warnings at the YAML validation layer (`kpi` output).
- valid=True, errors=0 (warning-only, not error).

### Coverage (run_pilot L3 results)

| Category | KAR | FGR | Assertions |
|---|---|---|---|
| infrastructure | 100% | 0% | 0 |
| dependencies  | 100% | 0% | 0 |
| endpoints     | 100% | 0% | 0 |
| agents        | 100% | 100% | 28 |
| **Total**     | 100% | 100% | 28 |

**Reading note** (this is why the report is split by plane):
the global FGR of 100% is carried by the single category (`agents`)
that produced assertions. The other three categories returned
"no encontrado" for every question, so FGR=0% per category. The
aggregate figure, taken alone, hides the by-category shortfall.

The shortfall occurs because the pilot asks about `Ollama`,
`MySQL`, `app-server-01` — entities the dataset does not contain.
The tools correctly reported absence; the dataset does not yet
cover those names.

### Topological state

- 53 entities indexed.
- 51 relations in graph.
- 6 asset, 2 automation, 10 endpoint, 6 agent, 29 software.
- Indexes: id=53, kind=5, forward_relation=51, reverse_relation=51.

## Performance — ¿cómo respondió la ejecución?

These are timing observations only.

### Per-call latency observed

- `cmdb_get(adguardhome-54)` first call: ~815ms (cold start).
- Subsequent `cmdb_get` calls in the same audit: ~0ms.
- `cmdb_reload()` end-to-end: ~815ms (full reload cycle).
- `run_pilot` PILOT METRICS: avg 51ms, P95 815ms.

### Hypotheses for the cold-start ~815ms

These are not investigated yet — listed as candidate causes only;
the first that fits will be looked at when an EP-worthy recurrence
appears.

- YAML load on first access.
- Index construction at first query.
- Cache warming.
- Python interpreter + module import cold start.

The 815ms shows up consistently as the **first** call of a given
shape in a given run, not as a per-call cost. That is
characteristic of cold-start mechanisms.

## Status

This audit is **the first run**. Findings recorded under
`consumers/inspector/NOTES.md → "Audit findings"` are kept at
information-level, not promoted to EP or PI.

A second audit, with qualitatively the same findings, is the
smallest evidence that would justify promoting one of them to EP.
Until then, no architectural change is proposed.