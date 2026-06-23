---
name: agent-cmdb
description: Ground AI agent responses in verified infrastructure facts — consult CMDB before asserting, reduce hallucinations, cite sources.
category: agent-tooling
version: 1.0.0
author: Carlos Cáceres
license: MIT
tags: [grounding, cmdb, facts, infrastructure, hallucination-prevention]

---

# Agent-CMDB Skill Interface

**Factual memory layer for AI agents** — обеспечивает grounding с проверенными фактами инфраструктуры.

## Purpose

Prevent AI agents from:
- Inventing servers that don't exist
- Forgetting critical dependencies
- Assuming outdated configurations
- Repeating questions across sessions
- Losing knowledge between conversations

## Core Principle

> An agent should not **remember** infrastructure; it should **query** a verifiable representation of reality before reasoning.

## Contract: What This Skill Provides

### 1. Factual Grounding (NOT Opinions)

Agent-CMDB returns **facts with evidence**:

```python
{
  "exists": True,
  "entity": {
    "id": "ollama",
    "kind": "software",
    "status": "operational"
  },
  "evidence": {
    "source_file": "software/ollama.yaml",
    "validated": True,
    "confidence_level": "verified",
    "entity_hash": "sha256:abc123..."
  }
}
```

**NOT**:
```python
{
  "answer": "Ollama is critical"  # Opinion, not fact
}
```

### 2. Explicit Uncertainty

Agents know **why** to trust facts:

- `confidence_level`: `verified` | `declared` | `discovered` | `inferred` | `unknown`
- `evidence.source_type`: `declared` (human YAML) vs `discovered` (scanner) vs `inferred` (reasoning)
- `observed_at`: When fact was verified
- `expires_at`: When confidence expires (TTL by source type)

### 3. Temporal Awareness

Facts expire. Agents can detect staleness:

```python
if not evidence.is_fresh():
    print("⚠️ This fact may be stale")
    print(f"  Observed: {evidence.observed_at}")
    print(f"  Expires: {evidence.expires_at}")
```

### 4. Change Detection

Detect if facts changed between queries:

```python
hash_before = result.evidence.entity_hash
# ... time passes ...
hash_after = new_result.evidence.entity_hash

if hash_before != hash_after:
    print("Entity changed — re-evaluate assumptions")
```

## Available Tools

### Grounding (Always Use Before Asserting)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_exists(entity_id)` | Check if entity exists | Before making ANY factual claim |
| `cmdb_get(entity_id)` | Get full entity with evidence | When reasoning about specific entity |
| `cmdb_assert(entity_id, kind, status)` | Binary validation | When decision requires specific state |
| `cmdb_search(query)` | Find entities matching query | When entity ID unknown |

### Context (Avoid 20 Sequential Queries)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_context(agent_id)` | Pre-packaged context for agent | On agent startup |

### Impact Analysis (Before Actions)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_impact(entity_id)` | Dependency graph analysis | BEFORE modifying anything |

### Utility

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cmdb_list(kind, status)` | List entities by filter | Discovery, enumeration |

## Behavioral Rules (MANDATORY)

### Rule 1: Never Invent Infrastructure

**WRONG:**
> "MySQL runs on server-42" (without verifying)

**CORRECT:**
```python
result = cmdb_exists("mysql")
if result.exists:
    # Now safe to reference
    print(f"MySQL is in CMDB")
else:
    # Explicit absence
    print("MySQL not found in CMDB — cannot verify this claim")
```

### Rule 2: Always Check Confidence

**WRONG:**
> "Ollama runs on server-53" (stating as absolute truth)

**CORRECT:**
```python
result = cmdb_get("ollama")
evidence = result.evidence

if evidence.confidence_level == "verified":
    print("Ollama runs_on server-53 (verified by schema v1)")
elif evidence.confidence_level == "inferred":
    print("Ollama likely runs_on server-53 (inferred, may be incomplete)")
else:
    print(f"Ollama status unknown (confidence: {evidence.confidence_level})")
```

### Rule 3: Cite Sources

**WRONG:**
> "The database is MySQL"

**CORRECT:**
> "According to `data/mysql-db.yaml` (validated), the database is MySQL"

### Rule 4: Report Uncertainty Explicitly

**WRONG:**
> "I'm not sure" (vague)

**CORRECT:**
> "confidence_level='declared' — YAML exists but not validated against schema v1"

### Rule 5: Check Impact Before Modifying

**ALWAYS:**
```python
impact = cmdb_impact("ollama")

if impact["risk_indicators"]["single_point_of_failure"]:
    print("⚠️ Ollama has no redundancy")
    print(f"  Affected: {impact['risk_indicators']['total_dependents']} dependents")
    print(f"  Critical: {len(impact['risk_indicators']['critical_dependents'])}")
    print("\nRecommend: Schedule maintenance window, notify users")
```

**NEVER:**
> Modify infrastructure without checking impact first.

## Usage Examples

### Example 1: Verify Before Answering

**User:** "¿Qué servidor corre Ollama?"

**Agent (WRONG):**
> "Ollama corre en server-53" (assumes from memory)

**Agent (CORRECT):**
```python
result = cmdb_get("ollama")

if result.exists and result.evidence.confidence_level == "verified":
    print(f"Ollama runs on {result.entity.metadata.get('runs_on')} (verified)")
else:
    print("Cannot verify — Ollama not in CMDB or evidence level low")
```

### Example 2: Action with Impact Check

**User:** "Voy a actualizar Ollama"

**Agent (WRONG):**
> "Ok, procedo" (no impact analysis)

**Agent (CORRECT):**
```python
# Step 1: Verify existence
assertion = cmdb_assert("ollama", expected_kind="software")
if not assertion["valid"]:
    print(f"⚠️ Cannot proceed: {assertion['reason']}")
    return

# Step 2: Check impact
impact = cmdb_impact("ollama")

print("📊 Impact Analysis:")
print(f"  Direct dependents: {len(impact['depends_on_me']['direct'])}")
print(f"  Critical dependents: {len(impact['risk_indicators']['critical_dependents'])}")
print(f"  Single point of failure: {impact['risk_indicators']['single_point_of_failure']}")

if impact["risk_indicators"]["single_point_of_failure"]:
    print("\n⚠️ RISK: No redundancy found")
    print("Recommend: Schedule maintenance window, notify users first")
```

### Example 3: Startup with Full Context

**Agent initialization:**

```python
# Single call instead of 20 sequential queries
ctx = cmdb_context("hermes-arquitectobi")

print(f"Identity: {ctx['identity']}")
print(f"Status: {ctx['known_environment']['status']}")
print(f"I run on: {ctx['known_environment']['runs_on']}")
print(f"I use: {ctx['known_environment']['uses']}")
print(f"Dependents: {ctx['dependents']}")
print(f"Warnings: {ctx['warnings']}")
```

**Benefits:**
- Knows itself immediately
- Aware of dependencies
- Warned about SPOFs
- No hallucination risk at startup

### Example 4: Temporal Reasoning

**User:** "¿Esto era cierto hace una hora?"

**Agent:**
```python
result = cmdb_get("ollama")
evidence = result.evidence

if evidence.is_fresh():
    print(f"✓ Fact is fresh (observed {evidence.observed_at})")
else:
    age = evidence.age_seconds() / 3600  # hours
    print(f"⚠️ Fact is {age:.1f} hours old")
    print(f"  Expires: {evidence.expires_at}")
    print("  Consider re-verifying before acting")
```

## Separation of Concerns

### Agent-CMDB (This Skill)

**Provides:**
- Facts: "ollama runs_on server-53"
- Evidence: Why trust this fact
- Confidence: Quality level
- Impact: Dependency graph

**NEVER Provides:**
- Recommendations: "Don't update Ollama"
- Opinions: "This is risky"
- Decisions: "You should wait"

### Agent (LLM)

**Responsibilities:**
- Interpret facts
- Weigh risks
- Make recommendations
- Decide actions

**Example Flow:**

```
Agent-CMDB → Facts + Evidence
                 ↓
              Agent (LLM)
                 ↓
         Interpretation + Decision
                 ↓
         "Recommend: Wait, notify users"
```

## Anti-Patterns to Avoid

### ❌ Pattern 1: Stating Facts Without Verification

```python
# WRONG
print("MySQL is on server-42")

# CORRECT
if cmdb_exists("mysql").exists:
    print("MySQL exists in CMDB")
else:
    print("MySQL not in CMDB — cannot verify")
```

### ❌ Pattern 2: Ignoring Confidence Level

```python
# WRONG
result = cmdb_get("ollama")
print(f"Ollama is {result.entity.status}")  # No confidence check

# CORRECT
result = cmdb_get("ollama")
if result.evidence.confidence_level == "verified":
    print(f"Ollama is {result.entity.status} (verified)")
else:
    print(f"Confidence: {result.evidence.confidence_level}")
```

### ❌ Pattern 3: Acting Without Impact Analysis

```python
# WRONG
# User: "Delete redis"
terminal("redis-cli shutdown")

# CORRECT
impact = cmdb_impact("redis")
if len(impact["depends_on_me"]["direct"]) > 0:
    print(f"⚠️ {len(impact['depends_on_me']['direct'])} entities depend on redis")
    print("Confirm deletion?")
```

### ❌ Pattern 4: Mixing Facts with Opinions

**WRONG response:**
> "MySQL runs on server-42 and this is dangerous"

(First part = fact, second part = opinion)

**CORRECT response:**
> "MySQL runs_on server-42 (source: `data/mysql.yaml`, validated)"
> 
> Additional observation (agent opinion):
> "Running MySQL on a single server creates SPOF risk"

## Confidence Levels Reference

| Level | Meaning | When Used |
|-------|---------|-----------|
| `verified` | Validated against schema v1 | Human-maintained YAML passed validation |
| `declared` | exists in source, not validated | YAML exists but schema validation pending |
| `discovered` | Auto-discovered | Docker/K8s scan result |
| `inferred` | Deduced by reasoning engine | Not directly observed |
| `unknown` | Minimal/no evidence | Unknown origin |

## Source Types Reference

| Type | Description | TTL | Example |
|------|-------------|-----|---------|
| `declared` | Human-maintained YAML | None (stable) | `software/ollama.yaml` |
| `discovered` | Auto-discovered (scanner) | 1 hour | Docker container scan |
| `imported` | External API | 5 minutes | AWS EC2 API |
| `inferred` | Reasoning engine | 1 minute | Deduced from logs |

## Testing

Run tests:

```bash
cd integrations/hermes/tests
python -m pytest
```

## Future Integrations

This skill is framework-agnostic. Future integrations:

- **OpenClaw**: Same core, different tool registration
- **LangGraph**: Graph-based agent workflows
- **AutoGen**: Multi-agent scenarios
- **CrewAI**: Role-based agent teams

All share the same core: `cmdb/` factual layer.

## changelog

### v1.0.0 (2026-06-22)

- Initial release
- `cmdb_exists`, `cmdb_get`, `cmdb_search`, `cmdb_list`
- `cmdb_assert`, `cmdb_context`
- `cmdb_impact`
- Evidence with `observed_at`, `expires_at`, `ttl_seconds`
- Confidence levels: `verified`/`declared`/`discovered`/`inferred`/`unknown`
- Source types: `declared`/`discovered`/`imported`/`inferred`