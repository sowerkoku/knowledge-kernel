import os
from typing import Optional, Union
from pathlib import Path
from datetime import datetime
import json
import hashlib

from .validator import cmdb_validate
from .config import get_config
from .engine import get_engine, Entity as EngineEntity
from .models import (
    Entity as ModelEntity,
    Evidence,
    QueryContext,
    CMDBResult,
    ConfidenceLevel,
    EvidenceBasis,
    SourceType,
)

from .taxonomy import ALL_KINDS, VALID_DOMAINS, KIND_TO_DOMAIN


def get_default_entities_dir() -> Path:
    """Get default entities directory from centralized config."""
    return get_config().data_dir


DEFAULT_ENTITIES_DIR = get_default_entities_dir()


def _compute_entity_hash(entity: dict) -> str:
    """Compute deterministic hash of entity for change detection."""
    # Only hash the stable fields
    stable = {
        "id": entity.get("id"),
        "kind": entity.get("kind"),
        "status": entity.get("status"),
        "metadata": entity.get("metadata", {}),
        "relations": entity.get("relations", []),
        "criticality": entity.get("criticality", {}),
        "schema_version": entity.get("schema_version"),
    }
    serialized = json.dumps(stable, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def _extract_facts(entity: dict) -> list[str]:
    """Extract natural language facts from an entity."""
    facts = []
    metadata = entity.get("metadata", {})

    # Base fact
    kind = entity.get("kind", "unknown")
    entity_id = entity.get("id", "unknown")
    facts.append(f"{kind.title()} entity: {entity_id}")

    # Status
    if entity.get("status"):
        facts.append(f"Status: {entity['status']}")

    # Metadata
    if metadata.get("name"):
        facts.append(f"Name: {metadata['name']}")

    if metadata.get("version"):
        facts.append(f"Version: {metadata['version']}")

    if metadata.get("description"):
        desc = metadata["description"]
        if len(desc) > 100:
            desc = desc[:100] + "..."
        facts.append(f"Description: {desc}")

    return facts


def _group_relations(entity: dict) -> dict:
    """Group relations by type, including reverse relations."""
    relations = {
        "runs_on": [],
        "uses": [],
        "reads": [],
        "writes": [],
        "calls": [],
        "owns": [],
        "backs_up": [],
        "monitors": [],
        "exposes": [],
        "exposed_by": [],
    }

    for rel in entity.get("relations", []):
        rel_type = rel.get("type")
        rel_target = rel.get("target")

        if rel_type in relations:
            relations[rel_type].append(rel_target)

    # Remove empty
    return {k: v for k, v in relations.items() if v}


def _derive_criticality(entity: dict) -> Optional[dict]:
    """Derive criticality classification from entity data."""
    criticality = entity.get("criticality", {})

    if not criticality:
        return None

    return {
        "business": criticality.get("business", "medium"),
        "operational": criticality.get("operational", "medium"),
        "technical": criticality.get("technical", "medium"),
    }


def _entity_to_dict(entity: EngineEntity) -> dict:
    """Convert EngineEntity to dict for compatibility."""
    return {
        "id": entity.id,
        "kind": entity.kind,
        "status": entity.status,
        "metadata": entity.metadata,
        "relations": [{"type": r.type, "target": r.target} for r in entity.relations],
        "criticality": entity.criticality,
        "schema_version": entity.schema_version,
    }


def _build_evidence(entity: EngineEntity, entity_file: str) -> Evidence:
    """Build Evidence object from entity and file."""
    is_validated = entity.schema_version == 1
    confidence_level = ConfidenceLevel.HIGH if is_validated else ConfidenceLevel.MEDIUM
    confidence_reasons = []
    confidence_basis = []

    if is_validated:
        confidence_reasons.append("yaml_validated_schema_v1")
        confidence_basis.append(EvidenceBasis.SCHEMA_VALIDATED)
        confidence_basis.append(EvidenceBasis.HUMAN_DECLARED)
    else:
        schema_ver = entity.schema_version
        if schema_ver:
            confidence_reasons.append(f"schema_v{schema_ver}")
            confidence_basis.append(EvidenceBasis.SCHEMA_VALIDATED)
        else:
            confidence_reasons.append("no_schema_version")
        confidence_basis.append(EvidenceBasis.HUMAN_DECLARED)

    if entity.status:
        confidence_reasons.append("status_declared")

    if entity.relations:
        confidence_reasons.append("relations_defined")

    return Evidence(
        source_type=SourceType.DECLARED,
        source_file=str(entity_file),
        source_type_label="cmdb_yaml",
        schema_version=entity.schema_version,
        validated=is_validated,
        entity_hash=_compute_entity_hash(_entity_to_dict(entity)),
        confidence_level=confidence_level,
        confidence_basis=confidence_basis,
    )


def _engine(entities_dir: Optional[Path] = None):
    """Get engine instance for given directory."""
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    return get_engine(entities_dir)


def cmdb_get(entity_id: str, entities_dir: Optional[Path] = None) -> CMDBResult:
    """
    Get a single entity by ID with full context for agent reasoning.

    Returns CMDBResult with separated:
    - entity: declared reality
    - evidence: why we trust it
    - context: when queried
    """
    engine = _engine(entities_dir)

    # Query context (query-time metadata)
    context = QueryContext(
        entities_dir=str(entities_dir) if entities_dir else None,
    )

    entity = engine.get_by_id(entity_id)

    if entity is None:
        # Fallback to old behavior for similar_entities (needs full scan)
        all_ids = engine.list_all_ids()
        similar = [eid for eid in all_ids if entity_id.lower() in eid.lower()][:5]
        return CMDBResult(
            exists=False,
            entity_id=entity_id,
            reason="Entity not found in CMDB",
            similar_entities=similar,
            context=context,
        )

    # Build file path for evidence
    entity_file = entity.source_file or "unknown"

    # Build Entity object (model)
    entity_obj = ModelEntity(
        id=entity.id,
        kind=entity.kind,
        status=entity.status,
        metadata=entity.metadata,
        relations=entity.relations,
    )

    evidence = _build_evidence(entity, entity_file)

    return CMDBResult(
        exists=True,
        entity=entity_obj,
        evidence=evidence,
        context=context,
    )


def cmdb_search(query: str, entities_dir: Optional[Path] = None) -> list[dict]:
    """
    Search entities by name, description, or tags (case-insensitive).

    **Agent usage:**
    Use this when the user mentions something but you're not sure of the exact ID.
    Always search before assuming non-existence.

    ```python
    results = cmdb_search("telegram")
    if results:
        print(f"Found {len(results)} entities:")
        for r in results:
            print(f"  - {r['id']} ({r['kind']})")
    else:
        print("No entities found — ask for clarification")
    ```

    Args:
        query: Search term (e.g., "telegram", "mysql", "backup")
        entities_dir: Path to entities directory

    Returns:
        List of matching entities with match info.

        Example:
        ```python
        [
            {
                "id": "telegram-api",
                "kind": "software",
                "domain": "software",
                "metadata": {"name": "Telegram Bot API"},
                "status": "operational",
                "match_field": "metadata.name",
                "score": 1.0
            },
            ...
        ]
        ```
    """
    engine = _engine(entities_dir)
    query_lower = query.lower()

    results = []

    for entity_id in engine.list_all_ids():
        entity = engine.get_by_id(entity_id)
        if not entity:
            continue

        score = 0.0
        match_field = ""

        # ID match (highest priority)
        if query_lower in entity_id.lower():
            score = max(score, 1.0)
            match_field = "id"

        # Metadata.name
        metadata = entity.metadata or {}
        if metadata.get("name") and query_lower in metadata["name"].lower():
            score = max(score, 0.9)
            match_field = "metadata.name"

        # Metadata.description
        if metadata.get("description") and query_lower in metadata["description"].lower():
            score = max(score, 0.8)
            match_field = "metadata.description"

        # Metadata.version
        if metadata.get("version") and query_lower in str(metadata["version"]).lower():
            score = max(score, 0.7)
            match_field = "metadata.version"

        # Tags
        tags = metadata.get("tags", [])
        for tag in tags:
            if query_lower in str(tag).lower():
                score = max(score, 0.7)
                match_field = "metadata.tags"

        # Search all other scalar metadata fields (IP addresses, ports, hostnames, etc.)
        for key, value in metadata.items():
            if key in ("name", "description", "version", "tags"):
                continue  # Already handled above
            if isinstance(value, (str, int, float, bool)):
                if query_lower in str(value).lower():
                    score = max(score, 0.6)
                    match_field = f"metadata.{key}"
                    break

        # Relations
        for rel in entity.relations:
            target = rel.target
            if query_lower in target.lower():
                score = max(score, 0.75)
                match_field = f"relations[].target ({target})"
                break

        if score > 0:
            results.append({
                "id": entity_id,
                "kind": entity.kind,
                "domain": KIND_TO_DOMAIN.get(entity.kind),
                "metadata": metadata,
                "status": entity.status,
                "match_field": match_field,
                "score": score,
            })

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    return results


def cmdb_list(kind: Optional[str] = None, status: Optional[str] = None, domain: Optional[str] = None, entities_dir: Optional[Path] = None) -> list[dict]:
    """
    List entities, optionally filtered by kind, status, and/or domain.

    **Agent usage:**
    Use this to enumerate all entities of a type or status.

    ```python
    # List all software
    software = cmdb_list(kind="software")

    # List all operational infrastructure
    infra = cmdb_list(domain="infrastructure", status="operational")

    # List everything that's down
    down = cmdb_list(status="down")
    ```

    Args:
        kind: Filter by kind (asset, software, procedure, etc.)
        status: Filter by status (operational, degraded, down, deprecated)
        domain: Filter by domain (infrastructure, software, knowledge, organization)
        entities_dir: Path to entities directory

    Returns:
        List of entity dicts (without full relations for brevity).
    """
    engine = _engine(entities_dir)

    # Fast path: kind filter
    if kind:
        entities = engine.get_by_kind(kind)
    else:
        entities = [engine.get_by_id(eid) for eid in engine.list_all_ids()]

    results = []
    for entity in entities:
        if not entity:
            continue
        if status and entity.status != status:
            continue
        if domain and KIND_TO_DOMAIN.get(entity.kind) != domain:
            continue

        # Return abbreviated entity (exclude heavy fields)
        results.append({
            "id": entity.id,
            "kind": entity.kind,
            "domain": KIND_TO_DOMAIN.get(entity.kind),
            "metadata": entity.metadata or {},
            "status": entity.status,
        })

    return results


def cmdb_validate(entities_dir: Optional[Path] = None) -> dict:
    """
    Validate all entities in the CMDB.

    **Agent usage:**
    Use this to check CMDB health before making assertions.
    If validation fails, warn the user that facts may be unreliable.

    ```python
    health = cmdb_validate()
    if not health["valid"]:
        print(f"⚠️  CMDB has {len(health['errors'])} errors — facts may be unreliable")
    ```

    Args:
        entities_dir: Path to entities directory

    Returns:
        Validation result with:
        - valid: bool
        - errors: list of error dicts
        - warnings: list of warning dicts
        - stats: counts by kind and status
    """
    from .validator import cmdb_validate as validator_cmdb_validate
    entities_dir = entities_dir or DEFAULT_ENTITIES_DIR
    return validator_cmdb_validate(entities_dir)


def cmdb_exists(entity_id: str, entities_dir: Optional[Path] = None) -> dict:
    """
    Check if an entity exists in the CMDB.

    **Agent usage:**
    Use this BEFORE making any factual claim about an entity.
    If it doesn't exist, don't hallucinate — ask or search.

    ```python
    if not cmdb_exists("my-server")["exists"]:
        print("Entity not found — ask user for clarification")
    ```

    Args:
        entity_id: Entity ID to check
        entities_dir: Path to entities directory

    Returns:
        {"exists": bool, "entity_id": str}
    """
    engine = _engine(entities_dir)
    entity = engine.get_by_id(entity_id)
    return {"exists": entity is not None, "entity_id": entity_id}