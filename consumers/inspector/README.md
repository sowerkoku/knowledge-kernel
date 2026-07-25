# Knowledge Inspector

Inspector consumes the public API of the [Knowledge Kernel](../..) and produces
falsifiable, deterministic findings. It is **not** part of the Kernel contract;
it is a consumer of that contract.

## Contract (five invariants)

1. Consumes only the public API of the Kernel (`cmdb.api.__all__`).
2. Is deterministic — `(dataset_hash, inspector_version, policy_version, parameters)`
   determine the report uniquely.
3. Separates contract (Kernel) from policy (Inspector).
4. Every finding is traceable and falsable
   (`evidence` + `policy` + `would_become_false_if`).
5. Produces findings, never architectural decisions.

## Quick start

```bash
# From the repo root:
PYTHONPATH=consumers/inspector python3 -m inspector.cli \
    --stale-after-days 90 \
    --output /tmp/inspector_report.json
```

## Layout

```
inspector/
  __init__.py         version + policy_version pins
  evidence.py         raw evidence collected from cmdb.api
  report.py           deterministic run + JSON serialization
  cli.py              CLI entry point
  rules/
    stale_entity.py   first rule (falsable, dated)
tests/
  test_inspector.py   determinism + falsability invariants
examples/             sample findings for documentation
```
