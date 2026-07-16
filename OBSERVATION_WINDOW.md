# L2.1 Observation Window — OPEN

**Date Opened:** 2026-07-12  
**Status:** OBSERVE MODE ACTIVE (BUILD=OFF)  
**Governance:** OBSERVE RULE 1 in effect

---

## Baseline Frozen

| Metric | Value |
|--------|-------|
| **Version** | v1.1.1 (search discoverability fix) |
| **Dataset Hash** | `ae4773b1` |
| **Entities** | 36 |
| **Relations** | 26 forward, 26 reverse |
| **Generation** | 1 (at window open) |
| **Memory** | 1 KB |
| **P95 Latency** | 1.18 ms |
| **Pilot Coverage** | 10/10 = 100% |

---

## Health Checks Passed

### ✅ Test Suite
```
25 passed
5 skipped (CIC-specific, intentional)
0 failed
```

### ✅ Dataset Hash Stability
```
Reload #1: hash=ae4773b1, generation=1
Reload #2: hash=ae4773b1, generation=2
Reload #3: hash=ae4773b1, generation=3

Stability:    ✅ Same dataset ⇒ Same hash
Independence: ✅ Same hash ⇏ Same generation
```

### ✅ Telemetry Instrumentation
```
~/.hermes/telemetry/kernel/queries.jsonl  → active
~/.hermes/telemetry/kernel/assertions.jsonl → active

Fields verified:
  - dataset_hash ✅
  - engine_generation ✅
  - schema_version ✅
  - kernel_version ✅
  - dataset_snapshot ✅
  - latency_ms ✅
```

---

## Observation Indicators (5 Primary)

| Indicator | Target | Current | Status |
|-----------|--------|---------|--------|
| **KAR** (Knowledge Accuracy Ratio) | >80% | TBD | Awaiting 100 queries |
| **FGR** (Fact Grounded Rate) | >90% | TBD | Awaiting 100 queries |
| **Fact Miss Rate** | <20% | TBD | Awaiting 100 queries |
| **API Distribution** | — | TBD | Awaiting 100 queries |
| **Dataset Churn** | Context-dependent | TBD | Awaiting window |

---

## Exit Criterion

**Observation window closes when:**
- ≥100 real queries accumulated
- ≥5 different Hermes agents have used the Kernel
- KAR and FGR have stabilized (variance <10% over last 20 queries)
- At least one architectural insight has emerged from evidence

**Expected close date:** 2026-08-14 (per GitHub Milestone #1)

---

## Rules During Observation

### Permitted (OBSERVE RULE 1)
- ✅ Fix bugs (defects only)
- ✅ Performance tuning (if it preserves public contracts)
- ✅ Dataset corrections (add missing facts, fix stale data)
- ✅ Documentation updates

### Forbidden (until exit criterion met)
- ❌ New indexes or caches
- ❌ Architectural redesign
- ❌ New public API functions
- ❌ Evidence engines
- ❌ Proposal queues
- ❌ Multi-writer semantics
- ❌ Prefetching or watchers

---

## Releases in Scope

| Tag | Commit | Description |
|-----|--------|-------------|
| v1.0.0 | `ed82cba` | Shared Factual Substrate (initial) |
| v1.1.0 | `742e437` | Deterministic Engine & Observability |
| v1.1.1 | `a4977c3` | Search Discoverability Fix |

---

## Files

- `~/knowledge-kernel/baselines/baseline-2026-07-12.md` — Initial baseline
- `~/knowledge-kernel/baselines/baseline-2026-07-12.json` — JSON baseline
- `~/knowledge-kernel/baselines/gaps-2026-07-12.json` — Gap analysis (all resolved)
- `~/.hermes/telemetry/kernel/queries.jsonl` — Live query log
- `~/.hermes/telemetry/kernel/assertions.jsonl` — Live assertion log

---

## Next Actions

1. **Hermes uses Kernel naturally** — no forced queries
2. **Telemetry accumulates** — passive observation
3. **Weekly review** — KAR, FGR, Fact Miss Rate trends
4. **Gap discoveries** — add to dataset, not architecture
5. **Exit review** — 2026-08-14 or when criterion met

---

**Motto (OBSERVE MODE):**

> "The purpose of OBSERVE MODE is not to prove that the current
> architecture is correct. Its purpose is to discover where
> reality disagrees with our assumptions."

---

**Declared:** 2026-07-12  
**Declaring Agent:** Hermes  
**Witness:** Kernel Maintainer  
**GitHub Milestone:** #1 (L2.1 Observation Window)