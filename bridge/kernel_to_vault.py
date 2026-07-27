#!/usr/bin/env python3
"""
Bridge: sync knowledge-kernel entities → Perseus Vault.

Reads entities from the knowledge-kernel CMDB and stores them in Perseus Vault
as structured memories for semantic recall, cross-session persistence, and
bi-temporal tracking.

Usage:
    # Sync all entities
    python bridge/kernel_to_vault.py --all

    # Sync by kind
    python bridge/kernel_to_vault.py --kind software
    python bridge/kernel_to_vault.py --kind asset --kind endpoint

    # Dry run (preview only)
    python bridge/kernel_to_vault.py --all --dry-run

    # Custom paths
    CMDB_DATA_DIR=~/knowledge/agent-cmdb \
    MIMIR_BINARY=/opt/data/webui/minions/.minions-data/mimir/mimir \
    MIMIR_DB=/opt/data/webui/minions-hermes-config/mimir.db \
    python bridge/kernel_to_vault.py --all

Requires:
    - knowledge-kernel installed (pip install -e .)
    - Perseus Vault binary available at MIMIR_BINARY
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---- Mimir MCP client (reuses the LangGraph adapter pattern) ----

class MimirClient:
    """Lightweight MCP stdio client for Perseus Vault."""

    def __init__(
        self,
        binary: str = "mimir",
        db_path: str = "~/.mimir/data/mimir.db",
        timeout: float = 30.0,
    ):
        self.binary = binary
        self.db_path = str(Path(db_path).expanduser())
        self.timeout = timeout
        self._proc: Optional[subprocess.Popen] = None
        self._req_id: int = 0
        self._lock = threading.Lock()

    def _ensure_session(self):
        if self._proc is not None and self._proc.poll() is None:
            return

        args = [self.binary, "serve", "--db", self.db_path]
        # Kill the idle watchdog so long syncs don't get reaped
        env = {**os.environ, "MIMIR_IDLE_TIMEOUT_SECS": "0"}

        self._proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        self._req_id = 0

        # MCP initialize handshake
        init_id = self._req_id + 1
        self._req_id = init_id
        init_req = json.dumps({
            "jsonrpc": "2.0", "id": init_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "kernel-to-vault-bridge", "version": "1.0.0"},
            },
        })
        try:
            self._proc.stdin.write(init_req + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError):
            self._proc = None
            raise RuntimeError("Failed to initialize Mimir process")

        self._read_response(init_id)

    def _read_response(self, expect_id: int) -> Optional[dict]:
        assert self._proc is not None
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                return None
            line = self._proc.stdout.readline()
            if not line:
                time.sleep(0.01)
                continue
            try:
                msg = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            if isinstance(msg, dict) and msg.get("id") == expect_id:
                return msg
        return None

    def _unwrap_result(self, result: dict) -> dict:
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured
        content = result.get("content")
        if isinstance(content, list) and content:
            text = content[0].get("text", "") if isinstance(content[0], dict) else ""
            try:
                parsed = json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    def call(self, method: str, params: dict) -> dict:
        with self._lock:
            try:
                self._ensure_session()
            except RuntimeError as e:
                raise RuntimeError(f"Mimir session failed: {e}")

            req_id = self._req_id + 2
            call_req = json.dumps({
                "jsonrpc": "2.0", "id": req_id,
                "method": "tools/call",
                "params": {"name": method, "arguments": params},
            })

            try:
                self._proc.stdin.write(call_req + "\n")
                self._proc.stdin.flush()
                self._req_id = req_id
            except (BrokenPipeError, OSError):
                self._proc = None
                raise RuntimeError("Mimir process died during call")

            response = self._read_response(req_id)
            if response is None:
                self._close()
                raise RuntimeError(f"No response from Mimir for {method}")
            if response.get("error"):
                raise RuntimeError(f"Mimir error ({method}): {response['error']}")
            return self._unwrap_result(response.get("result", {}))

    def remember(self, category: str, key: str, content: str,
                 provenance: Optional[dict] = None) -> dict:
        """Store an entity in Perseus Vault. Uses skip_dedup to avoid
        content-similarity dedup eating distinct facts.

        provenance dict carries kernel evidence chain fields:
          kernel_entity_id, dataset_hash, observed_at, entity_hash,
          source_file, confidence_level
        """
        body = {"content": content}
        if provenance:
            body["provenance"] = provenance
        return self.call("perseus_vault_remember", {
            "category": category,
            "key": key,
            "body_json": json.dumps(body),
            "skip_dedup": True,
        })

    def recall(self, query: str, category: str = "", limit: int = 5) -> dict:
        return self.call("perseus_vault_recall", {
            "query": query,
            "category": category,
            "mode": "fts5",
            "limit": limit,
        })

    def _close(self):
        if self._proc is None:
            return
        try:
            self._proc.stdin.close()
        except OSError:
            pass
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait()
        self._proc = None

    def __del__(self):
        self._close()


# ---- Entity formatting ----

def entity_to_vault_content(entity_id: str, kind: str, metadata: dict,
                            status: str, relations: list, tags: list,
                            provenance: Optional[dict] = None,
                            dataset_hash: str = "") -> str:
    """Format a kernel entity as a human-readable vault memory with provenance."""
    lines = [f"# {kind.title()}: {entity_id}"]

    if metadata.get("name"):
        lines.append(f"**Name:** {metadata['name']}")
    if metadata.get("description"):
        lines.append(f"**Description:** {metadata['description']}")
    if metadata.get("version"):
        lines.append(f"**Version:** {metadata['version']}")

    # Endpoint-specific metadata
    for field in ("host", "port", "protocol"):
        if field in metadata:
            lines.append(f"**{field.title()}:** {metadata[field]}")

    # Asset specs
    if "specs" in metadata:
        specs = metadata["specs"]
        spec_str = ", ".join(f"{k}: {v}" for k, v in specs.items())
        lines.append(f"**Specs:** {spec_str}")

    if status:
        lines.append(f"**Status:** {status}")

    if relations:
        rel_strs = [f"{r['type']} → {r['target']}" for r in relations]
        lines.append(f"**Relations:** {', '.join(rel_strs)}")

    if tags:
        lines.append(f"**Tags:** {', '.join(tags)}")

    # Provenance footer — distinguishes kernel facts from vague memories
    if provenance:
        lines.append("")
        lines.append("---")
        lines.append("**🔗 Kernel Provenance** _(verified fact from knowledge-kernel)_")
        if provenance.get("confidence_level"):
            lines.append(f"- Confidence: {provenance['confidence_level']}")
        if provenance.get("entity_hash"):
            lines.append(f"- Entity hash: {provenance['entity_hash']}")
        if provenance.get("observed_at"):
            lines.append(f"- Observed: {provenance['observed_at']}")
        if provenance.get("source_file"):
            lines.append(f"- Source: {provenance['source_file']}")
        if provenance.get("validated"):
            lines.append("- Schema validated: ✓")
        if dataset_hash:
            lines.append(f"- Dataset: {dataset_hash}")

    return "\n".join(lines)


# ---- Sync logic ----

def sync_kernel_to_vault(
    mimir: MimirClient,
    entities_dir: str,
    kinds: Optional[list[str]] = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Sync knowledge-kernel entities to Perseus Vault.

    Each Vault entity now carries kernel provenance metadata:
      kernel_entity_id, dataset_hash, observed_at, entity_hash,
      source_file, confidence_level

    Returns summary dict with counts.
    """
    # Import cmdb after path setup
    sys.path.insert(0, str(Path(__file__).parent.parent))
    os.environ.setdefault("CMDB_DATA_DIR", entities_dir)

    from cmdb.api import cmdb_list, cmdb_get, cmdb_stats

    # Get stats for dataset_hash (canonical kernel state identifier)
    stats = cmdb_stats(Path(entities_dir))
    dataset_hash = stats.get("dataset_hash", "")
    if verbose:
        print(f"Kernel stats: {json.dumps(stats, indent=2)}")
        print(f"Dataset hash: {dataset_hash}")

    # List entities
    all_entities = []
    if kinds:
        for kind in kinds:
            all_entities.extend(cmdb_list(kind=kind, entities_dir=Path(entities_dir)))
    else:
        all_entities = cmdb_list(entities_dir=Path(entities_dir))

    if verbose:
        print(f"Found {len(all_entities)} entities to sync")

    results = {"synced": 0, "skipped": 0, "errors": 0, "details": []}

    for entity_summary in all_entities:
        entity_id = entity_summary["id"]
        kind = entity_summary["kind"]
        category = f"kernel/{kind}"

        try:
            # Get full entity with evidence
            full = cmdb_get(entity_id, entities_dir=Path(entities_dir))
            if not full.exists:
                results["skipped"] += 1
                results["details"].append({
                    "id": entity_id, "status": "skipped",
                    "reason": "entity not found in full lookup"
                })
                continue

            entity = full.entity
            content = entity_to_vault_content(
                entity_id=entity_id,
                kind=kind,
                metadata=entity_summary.get("metadata", {}),
                status=entity_summary.get("status", ""),
                relations=[r.to_dict() for r in entity.relations] if hasattr(entity, 'relations') and entity.relations else [],
                tags=entity_summary.get("metadata", {}).get("tags", []),
                provenance=full.evidence.to_dict() if full.evidence else {},
                dataset_hash=dataset_hash,
            )

            # Build provenance for structured recall
            evidence = full.evidence
            provenance = {
                "kernel_entity_id": entity_id,
                "dataset_hash": dataset_hash,
            }
            if evidence:
                provenance["observed_at"] = evidence.observed_at
                provenance["entity_hash"] = evidence.entity_hash
                provenance["source_file"] = evidence.source_file
                provenance["confidence_level"] = evidence.confidence_level.value
                provenance["source_type"] = evidence.source_type.value
                provenance["validated"] = evidence.validated

            if dry_run:
                results["synced"] += 1
                results["details"].append({
                    "id": entity_id, "status": "would_sync",
                    "category": category, "size": len(content),
                    "provenance_hash": evidence.entity_hash if evidence else None,
                })
                if verbose:
                    print(f"  [DRY RUN] {entity_id} → {category} (hash={evidence.entity_hash[:8] if evidence and evidence.entity_hash else '?'})")
                continue

            resp = mimir.remember(category=category, key=entity_id,
                                  content=content, provenance=provenance)
            action = resp.get("action", "unknown")

            if action == "created":
                results["synced"] += 1
                results["details"].append({
                    "id": entity_id, "status": "created",
                    "category": category
                })
                if verbose:
                    print(f"  ✓ {entity_id} → {category}")
            elif action == "deduped (new key not created)":
                results["skipped"] += 1
                results["details"].append({
                    "id": entity_id, "status": "deduped",
                    "category": category
                })
                if verbose:
                    print(f"  ~ {entity_id} (deduped)")
            else:
                results["skipped"] += 1
                results["details"].append({
                    "id": entity_id, "status": action,
                    "category": category
                })
                if verbose:
                    print(f"  ? {entity_id} ({action})")

        except Exception as e:
            results["errors"] += 1
            results["details"].append({
                "id": entity_id, "status": "error",
                "error": str(e)
            })
            print(f"  ✗ {entity_id}: {e}", file=sys.stderr)

    return results


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(
        description="Sync knowledge-kernel entities to Perseus Vault"
    )
    parser.add_argument("--all", action="store_true", help="Sync all entity kinds")
    parser.add_argument("--kind", action="append", dest="kinds",
                        help="Sync specific kind (repeatable)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing to vault")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    parser.add_argument("--entities-dir", default=None,
                        help="Knowledge kernel data dir (env: CMDB_DATA_DIR)")
    parser.add_argument("--mimir-binary", default=None,
                        help="Path to mimir/perseus-vault binary")
    parser.add_argument("--mimir-db", default=None,
                        help="Path to mimir.db")

    args = parser.parse_args()

    if not args.all and not args.kinds:
        parser.error("Must specify --all or at least one --kind")

    # Paths
    entities_dir = args.entities_dir or os.environ.get(
        "CMDB_DATA_DIR", str(Path.home() / "knowledge" / "agent-cmdb")
    )
    mimir_binary = args.mimir_binary or os.environ.get(
        "MIMIR_BINARY", "/opt/data/webui/minions/.minions-data/mimir/mimir"
    )
    mimir_db = args.mimir_db or os.environ.get(
        "MIMIR_DB", "/opt/data/webui/minions-hermes-config/mimir.db"
    )

    if not Path(entities_dir).exists():
        print(f"Error: entities dir not found: {entities_dir}", file=sys.stderr)
        print("Set CMDB_DATA_DIR or use --entities-dir", file=sys.stderr)
        sys.exit(1)

    if not Path(mimir_binary).exists():
        print(f"Error: mimir binary not found: {mimir_binary}", file=sys.stderr)
        print("Set MIMIR_BINARY or use --mimir-binary", file=sys.stderr)
        sys.exit(1)

    print(f"Entities dir: {entities_dir}")
    print(f"Mimir binary: {mimir_binary}")
    print(f"Mimir DB:     {mimir_db}")
    if args.dry_run:
        print("MODE: DRY RUN (no writes)")
    print()

    kinds = args.kinds if args.kinds else None

    mimir = MimirClient(binary=mimir_binary, db_path=mimir_db)
    try:
        results = sync_kernel_to_vault(
            mimir=mimir,
            entities_dir=entities_dir,
            kinds=kinds,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    finally:
        mimir._close()

    print(f"\n--- Results ---")
    print(f"Synced:  {results['synced']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Errors:  {results['errors']}")
    print(f"Total:   {results['synced'] + results['skipped'] + results['errors']}")

    if results["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
