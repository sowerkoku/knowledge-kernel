"""
KernelEngine — In-memory indexed query engine.

L2 architecture: read-only deterministic derived indexes.

YAML  = canonical factual store (source of truth)
Memory = deterministic derived indexes (rebuildable)
API    = stable contract (cmdb.api)

Design choices:
- YAML loaded ONCE -> Entity objects in memory
- Indexes are reverse-lookup maps over those Entity objects
- No I/O on read path
- No write path exists (read-only)
- Thread-safe (single lock around reload; reads are GIL-safe)

Rejection of L3+ design:
- No proposal queues
- No distributed caches
- No evidence engines
- No mutation APIs

The only path to mutation is: edit YAML → reload().
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Dict, List, Optional, Set, Any
import yaml


# ---- Index primitives --------------------------------------------------

@dataclass(frozen=True)
class Relation:
    """A directed relation edge: source --type--> target."""
    type: str
    target: str

    def to_dict(self) -> dict:
        return {"type": self.type, "target": self.target}


@dataclass
class Entity:
    """In-memory representation of an entity. Mirrors YAML schema."""
    id: str
    kind: str
    metadata: dict
    status: Optional[str]
    relations: List[Relation]
    criticality: Optional[dict] = None
    tags: List[str] = field(default_factory=list)
    schema_version: Optional[int] = None
    source_file: Optional[str] = None
    raw: dict = field(default_factory=dict)

    def get(self, key: str, default=None):
        """Dict-style access for ergonomic API compatibility."""
        return getattr(self, key, default)


# ---- Engine ------------------------------------------------------------

@dataclass
class EngineConfig:
    """Engine configuration."""
    entities_dir: Path


@dataclass
class EngineStats:
    """Runtime statistics (post-load snapshot)."""
    entity_count: int
    by_kind: Dict[str, int]
    indexes_built_at: datetime
    load_wall_ms: int
    memory_estimate_kb: int


class KernelEngine:
    """
    In-memory indexed query engine.

    Thread-safe with a single RLock. Reads are O(1) on the dicts.
    The lock is only held during reload() (full rebuild).
    """

    _instances: Dict[str, "KernelEngine"] = {}
    _registry_lock = RLock()

    def __init__(self, config: EngineConfig):
        self.config = config
        self.entities_dir = config.entities_dir.expanduser().resolve()

        # Indexes
        self._id_index: Dict[str, Entity] = {}
        self._kind_index: Dict[str, Set[str]] = {}
        self._forward_relation_index: Dict[str, List[Relation]] = {}  # source -> [relations]
        self._reverse_relation_index: Dict[str, List[Relation]] = {}  # target -> [relations]

        self._stats: Optional[EngineStats] = None
        self._lock = RLock()

    @classmethod
    def get_instance(cls, entities_dir: Path) -> "KernelEngine":
        """Singleton-per-directory."""
        key = str(entities_dir.expanduser().resolve())
        with cls._registry_lock:
            if key not in cls._instances:
                cls._instances[key] = cls(EngineConfig(entities_dir=entities_dir))
            return cls._instances[key]

    @classmethod
    def clear_instance(cls, entities_dir: Optional[Path] = None) -> None:
        """Clear cached engine(s). Call if YAMLs changed since last load."""
        with cls._registry_lock:
            if entities_dir is None:
                cls._instances.clear()
            else:
                key = str(entities_dir.expanduser().resolve())
                cls._instances.pop(key, None)

    # ---- Load & reload --------------------------------------------------

    def ensure_loaded(self) -> None:
        """Lazy first-load. Safe to call repeatedly."""
        if self._stats is None:
            self.reload()

    def reload(self) -> EngineStats:
        """Rebuild indexes from YAML dataset. Read-only after this returns."""
        with self._lock:
            start = datetime.now()
            self._id_index.clear()
            self._kind_index.clear()
            self._forward_relation_index.clear()
            self._reverse_relation_index.clear()

            if not self.entities_dir.exists():
                self._stats = EngineStats(
                    entity_count=0,
                    by_kind={},
                    indexes_built_at=start,
                    load_wall_ms=0,
                    memory_estimate_kb=0,
                )
                return self._stats

            kind_counts: Dict[str, int] = {}
            count = 0

            for yaml_file in self.entities_dir.rglob("*.yaml"):
                try:
                    entity = self._load_yaml(yaml_file)
                    if entity is None:
                        continue
                    self._insert(entity)
                    kind_counts[entity.kind] = kind_counts.get(entity.kind, 0) + 1
                    count += 1
                except Exception:
                    # Skip unreadable/malformed files (validator handles errors separately)
                    continue

            elapsed = int((datetime.now() - start).total_seconds() * 1000)
            self._stats = EngineStats(
                entity_count=count,
                by_kind=kind_counts,
                indexes_built_at=start,
                load_wall_ms=elapsed,
                memory_estimate_kb=self._estimate_memory_kb(),
            )
            return self._stats

    def _load_yaml(self, yaml_file: Path) -> Optional[Entity]:
        """Parse one YAML file into Entity object."""
        with open(yaml_file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not raw or not isinstance(raw, dict):
            return None
        eid = raw.get("id")
        kind = raw.get("kind")
        if not eid or not kind:
            return None

        relations = [
            Relation(type=r.get("type", ""), target=r.get("target", ""))
            for r in raw.get("relations", [])
            if r.get("type") and r.get("target")
        ]

        return Entity(
            id=eid,
            kind=kind,
            metadata=raw.get("metadata", {}) or {},
            status=raw.get("status"),
            relations=relations,
            criticality=raw.get("criticality"),
            tags=raw.get("tags", []) or [],
            schema_version=raw.get("schema_version"),
            source_file=str(yaml_file),
            raw=raw,
        )

    def _insert(self, entity: Entity) -> None:
        """Insert entity into all indexes."""
        self._id_index[entity.id] = entity

        if entity.kind not in self._kind_index:
            self._kind_index[entity.kind] = set()
        self._kind_index[entity.kind].add(entity.id)

        if entity.id not in self._forward_relation_index:
            self._forward_relation_index[entity.id] = []
        self._forward_relation_index[entity.id].extend(entity.relations)

        for rel in entity.relations:
            if rel.target not in self._reverse_relation_index:
                self._reverse_relation_index[rel.target] = []
            # Reverse stores: this entity is the SOURCE from the perspective
            # of those who look up by TARGET->sources mapping.
            self._reverse_relation_index[rel.target].append(Relation(type=rel.type, target=entity.id))

    # ---- Queries (all O(1) on dicts) -----------------------------------

    def get_by_id(self, entity_id: str) -> Optional[Entity]:
        """O(1) lookup by ID."""
        self.ensure_loaded()
        with self._lock:
            return self._id_index.get(entity_id)

    def get_by_kind(self, kind: str) -> List[Entity]:
        """O(k) lookup by kind. Returns list of entities."""
        self.ensure_loaded()
        with self._lock:
            ids = self._kind_index.get(kind, set())
            return [self._id_index[i] for i in ids if i in self._id_index]

    def list_kinds(self) -> List[str]:
        """List all kinds present in dataset."""
        self.ensure_loaded()
        with self._lock:
            return sorted(self._kind_index.keys())

    def list_all_ids(self) -> List[str]:
        """List all entity IDs."""
        self.ensure_loaded()
        with self._lock:
            return sorted(self._id_index.keys())

    def get_all_entities(self) -> List[Entity]:
        """Return all entities as a list."""
        self.ensure_loaded()
        with self._lock:
            return list(self._id_index.values())

    def get_forward_relations(self, source_id: str) -> List[Relation]:
        """Relations FROM source: source --type--> target."""
        self.ensure_loaded()
        with self._lock:
            return list(self._forward_relation_index.get(source_id, []))

    def get_reverse_relations(self, target_id: str) -> List[Relation]:
        """Relations INTO target: source --type--> target (returns [(type, source_id)])."""
        self.ensure_loaded()
        with self._lock:
            # rel.target in this view actually contains the SOURCE id (see _insert)
            return list(self._reverse_relation_index.get(target_id, []))

    # ---- Stats ----------------------------------------------------------

    def get_stats(self) -> EngineStats:
        """Get engine statistics (forces load if needed)."""
        self.ensure_loaded()
        with self._lock:
            assert self._stats is not None, "Stats should be set after ensure_loaded()"
            return self._stats

    def _estimate_memory_kb(self) -> int:
        """Rough memory estimate by serializing indexes."""
        import json
        snapshot = {
            "ids": list(self._id_index.keys()),
            "kinds": {k: list(v) for k, v in self._kind_index.items()},
            "count": len(self._id_index),
        }
        return int(len(json.dumps(snapshot)) / 1024)


# ---- Public convenience ---------------------------------------------------

def get_engine(entities_dir: Path) -> KernelEngine:
    """Get or create engine instance."""
    return KernelEngine.get_instance(entities_dir)


def clear_engine_cache(entities_dir: Optional[Path] = None) -> None:
    """Force-clear engine. Call after editing YAML files."""
    KernelEngine.clear_instance(entities_dir)