# Test taxonomy

The repo's test suite is organised into four categories. Each one
guards a different kind of property:

| Category | What it protects | Examples in this repo |
|---|---|---|
| **Contract tests** | The Inspector protocol: Rule, Finding, KernelAPI. | `tests/test_contract.py`, `consumers/inspector/tests/test_contract.py` |
| **Behaviour tests** | Correctness of individual rules and reports. | `consumers/inspector/tests/test_inspector.py`, `tests/test_no_declared_relations.py` |
| **Boundary tests** | Architectural separation between layers. | `tests/test_consumers_boundary.py` |
| **Governance tests** | Repo conventions and cross-host invariants. | `tests/test_doc_governance.py` |

The categories were chosen for the kind of regression they catch:

- **Contract** failing means a public surface changed without notice.
- **Behaviour** failing means a rule's output is wrong.
- **Boundary** failing means a layer's dependency rules were violated.
- **Governance** failing means repo rituals drifted (e.g. SKILL.md
  de-sync between repo and runtime).

The numbers are secondary. The categories are the signal: as
the suite grows, *which of these four categories* is non-empty
tells you what's actually being protected.