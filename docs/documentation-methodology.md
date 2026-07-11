# Documentation Methodology for CIC Projects (Cico, 2026-07-07)

**Lesson from agent-cmdb v1.2 documentation rewrite.**

---

## Three Levels of Abstraction

A mature documentation system has exactly three levels:

| Level | Question | Content |
|-------|----------|---------|
| **1. Manifesto** | Why should I care? | README.md — the hook. Who it's for, what it solves, why it's different. Must be readable in <2 minutes. |
| **2. Philosophy + Architecture** | What is it and how does it work? | philosophy.md + architecture.md — canonical sources for principles and system structure. |
| **3. Operating** | How do I use and operate it? | domain-model.md, schema-v1.md, usage-patterns.md, governance.md, audit-methodology.md, error-log.md |

**Navigation diagram** in README.md helps new contributors find their level instantly.

---

## Canonical Homes (Single Source of Truth per Concept)

Each concept has **exactly one canonical document**. All other docs reference it.

| Concept | Canonical Home |
|---------|--------------|
| Design principles (6) | philosophy.md |
| KPIs (FGR, Coverage, Freshness) | philosophy.md |
| Pipeline (Kernel→Facts→Reasoning) | architecture.md |
| Code vs data separation | architecture.md |
| Asset/Software/Endpoint/Evidence | domain-model.md |
| YAML schema + validation | schema-v1.md |
| Entity inclusion criteria | governance.md |
| Why Not RAG / Why Not Memory | philosophy.md |

**If a concept appears in two documents, the second document should reference the first, not duplicate it.**

---

## Each Document Answers One Dominant Question

This is the most durable rule.

| Document | Dominant Question |
|----------|------------------|
| README.md | Why does this project exist? |
| philosophy.md | What principles govern it? |
| architecture.md | How do the pieces connect? |
| domain-model.md | What does it represent? |
| schema-v1.md | How is it serialized? |
| governance.md | What belongs to the Kernel? |
| usage-patterns.md | How is it queried? |
| audit-methodology.md | How do we verify quality? |
| error-log.md | How does it fail? |
| github-metadata.md | How is it positioned for discovery? |

**As the project grows, this rule keeps documentation navigable.**

---

## Cross-References Between Documents

Never let docs become islands. Every document's "See also" section links to:

- **Authoritative sources** (documents that define the concept, not just reference it)
- **Related documents** (documents that depend on or complement it)

Format:
```markdown
**Authoritative sources:**
- [`philosophy.md`](./philosophy.md) — principles and KPIs
- [`architecture.md`](./architecture.md) — system structure

**Related:**
- [`schema-v1.md`](./schema-v1.md) — YAML specification
```

---

## Positioning: How to Communicate the Project

**For agent-cmdb specifically:**

| Term | Usage |
|------|-------|
| **Knowledge Kernel** | Identity of the project — what it IS |
| **Deterministic Grounding** | Capability it provides — what it DOES |
| **"Shared source of truth"** | Core value proposition — multiple agents, same reality |
| **"Verified facts, evidence, relationships, freshness"** | Core components — the four things stored |

**Never compete in:** CMDB (NetBox/ServiceNow), RAG (vector DBs), Agent Memory (conversational). Own two concepts: Knowledge Kernel + Deterministic Grounding.

**For any project, Cico's checklist before publishing:**
1. README tagline: < 10 words, states the core differentiator
2. First paragraph: includes all key terms (facts, evidence, relationships, freshness)
3. "What it is NOT" section: preemptively answers the comparison questions
4. "When to use / When not to use" section: answers "is this for me?" in 30 seconds
5. GitHub description (160 chars): includes key search terms

---

## When to Refactor Documentation

- When a new concept requires a new document
- When an existing document answers more than one question
- When cross-references are broken or missing
- When the README no longer communicates the core value in <2 minutes
- When a visitor would not understand the project's identity after reading the README

**Not when:** adding features, changing code, fixing bugs. Documentation and code evolve separately.