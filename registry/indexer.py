"""
Registry Index — In-memory dual-graph store

Maintains:
  _by_id              → {id: entity_dict}
  _by_category        → {category: [id, ...]}
  _depends_on_index   → {id: set(depends_on ids)}
  _rdepends_index     → {id: set(dependents ids)}  # inverse of depends_on
  _runs_on_index      → {id: set(runs_on ids)}
  _rruns_on_index     → {id: set(entities that run_on this)}  # inverse
"""

from __future__ import annotations

import os
import yaml
import glob
from typing import Optional, Dict, List, Set, Any

REGISTRY_CATEGORIES = frozenset({
    "assets", "software", "data", "automation",
    "projects", "procedures", "endpoints",
})

# ─────────────────────────────────────────────────────────────
# Auto-detect which categories actually exist on disk.
# Whitelist of valid categories; only those present in the
# registry_path are active. Unrecognized directories are ignored.
# ─────────────────────────────────────────────────────────────

def _detect_categories(registry_path: str) -> frozenset:
    """Return frozenset of category names that exist as directories."""
    if not os.path.isdir(registry_path):
        return REGISTRY_CATEGORIES
    return frozenset(
        d for d in os.listdir(registry_path)
        if os.path.isdir(os.path.join(registry_path, d))
        and not d.startswith(".")
        and d in REGISTRY_CATEGORIES
    )


class RegistryIndex:
    """
    In-memory index for the Registry.
    
    Loads from /home/carlos/registry by default.
    Set REGISTRY_PATH env var to override.
    """

    def __init__(self, registry_path: Optional[str] = None):
        self.registry_path = registry_path or os.environ.get(
            "REGISTRY_PATH", "/home/carlos/registry"
        )
        self._categories = _detect_categories(self.registry_path)
        self._by_id: dict = {}
        self._by_category: dict = {cat: [] for cat in self._categories}
        self._depends_on_index: dict = {}
        self._rdepends_index: dict = {}  # inverse
        self._runs_on_index: dict = {}
        self._rruns_on_index: dict = {}  # inverse
        self._load()

    # ─────────────────────────────────────────────────────────────
    # Core indexing
    # ─────────────────────────────────────────────────────────────

    def _load(self):
        """Full reload of all YAML files."""
        self._by_id.clear()
        self._by_category = {cat: [] for cat in self._categories}

        self._depends_on_index.clear()
        self._rdepends_index.clear()
        self._runs_on_index.clear()
        self._rruns_on_index.clear()

        for category in self._categories:
            pattern = os.path.join(self.registry_path, category, "*.yaml")
            for filepath in glob.glob(pattern):
                basename = os.path.basename(filepath)
                if basename.startswith("README"):
                    continue
                with open(filepath, "r") as f:
                    entity = yaml.safe_load(f)
                self._index_entity(entity, category)

        self._build_derived_indices()

    def _index_entity(self, entity: dict, category: str):
        """Index a single entity into primary indices."""
        eid = entity["id"]
        self._by_id[eid] = entity
        self._by_category[category].append(eid)

        # Primary relations as sets
        depends = set(entity.get("relations", {}).get("depends_on", []))
        runs = set(entity.get("relations", {}).get("runs_on", []))

        self._depends_on_index[eid] = depends
        self._runs_on_index[eid] = runs

    def _build_derived_indices(self):
        """Build reverse indices from primary relations."""
        # Reverse depends_on
        self._rdepends_index.clear()
        for eid in self._depends_on_index:
            self._rdepends_index[eid] = set()

        for eid, deps in self._depends_on_index.items():
            for dep in deps:
                if dep not in self._rdepends_index:
                    self._rdepends_index[dep] = set()
                self._rdepends_index[dep].add(eid)

        # Reverse runs_on
        self._rruns_on_index.clear()
        for eid in self._runs_on_index:
            self._rruns_on_index[eid] = set()

        for eid, runs in self._runs_on_index.items():
            for host in runs:
                if host not in self._rruns_on_index:
                    self._rruns_on_index[host] = set()
                self._rruns_on_index[host].add(eid)

    # ─────────────────────────────────────────────────────────────
    # BFS traversal (depends_on only — functional graph)
    # ─────────────────────────────────────────────────────────────

    def _bfs_depends_on(self, eid: str, recursive: bool) -> list[str]:
        """BFS over depends_on edges."""
        if eid not in self._depends_on_index:
            return []
        result = set()
        queue = list(self._depends_on_index[eid])
        while queue:
            current = queue.pop(0)
            if current not in result and current in self._by_id:
                result.add(current)
                if recursive and current in self._depends_on_index:
                    queue.extend(self._depends_on_index[current])
        return sorted(result)

    def _bfs_dependents_of(self, eid: str, recursive: bool) -> list[str]:
        """Inverse BFS over depends_on (who depends on me)."""
        if eid not in self._rdepends_index:
            return []
        result = set()
        queue = list(self._rdepends_index[eid])
        while queue:
            current = queue.pop(0)
            if current not in result and current in self._by_id:
                result.add(current)
                if recursive and current in self._rdepends_index:
                    queue.extend(self._rdepends_index[current])
        return sorted(result)

    # ─────────────────────────────────────────────────────────────
    # Public API — get
    # ─────────────────────────────────────────────────────────────

    def get(self, id: str) -> Optional[dict]:
        """Get entity by ID."""
        return self._by_id.get(id)

    def list(self, category: Optional[str] = None) -> list[dict]:
        """
        List entities, optionally filtered by category.
        Returns summaries (not full entities).
        """
        if category is not None:
            if category not in self._categories:
                raise ValueError(f"Categoría inválida: {category}")
            ids = self._by_category.get(category, [])
        else:
            ids = list(self._by_id.keys())

        return [
            {
                "id": eid,
                "category": self._by_id[eid]["category"],
                "type": self._by_id[eid]["type"],
                "name": self._by_id[eid]["name"],
                "status": self._by_id[eid].get("status"),
                "tags": self._by_id[eid].get("tags", []),
            }
            for eid in sorted(ids)
        ]

    def search(self, query: str) -> list[dict]:
        """
        Search by text in id, name, description, tags.
        Returns matches with match_field and score.
        """
        q = query.lower()
        results = []

        for eid, entity in self._by_id.items():
            score = 0
            match_field = None

            # Exact match on id
            if q == eid.lower():
                score = 3
                match_field = "id"
            elif q in eid.lower():
                score = max(score, 2)
                match_field = match_field or "id"

            # Match on name
            name = entity.get("name", "")
            if q == name.lower():
                score = max(score, 3)
                match_field = match_field or "name"
            elif q in name.lower():
                score = max(score, 2)
                match_field = match_field or "name"

            # Match on description
            desc = entity.get("description", "")
            if q in desc.lower():
                score = max(score, 1)
                match_field = match_field or "description"

            # Match on tags
            tags = entity.get("tags", [])
            if any(q in tag.lower() for tag in tags):
                score = max(score, 1)
                match_field = match_field or "tags"

            if score > 0 and match_field:
                results.append({
                    "id": eid,
                    "name": name,
                    "category": entity["category"],
                    "match_field": match_field,
                    "score": score,
                })

        return sorted(results, key=lambda x: (-x["score"], x["id"]))

    def dependencies(self, id: str, recursive: bool = False) -> dict:
        """
        Get dependencies of an entity.

        Returns:
            {
                "functional": [{"id", "status", "type", "criticality"}, ...],
                "infrastructure": [{"id", "status", "type"}, ...]
            }
        """
        if id not in self._by_id:
            raise KeyError(f"Entidad no encontrada: {id}")

        # Functional: BFS over depends_on
        functional_ids = self._bfs_depends_on(id, recursive)

        # Infrastructure: 1-hop runs_on of this entity (not BFS)
        infrastructure_ids = sorted(self._runs_on_index.get(id, set()))

        return {
            "functional": [self._summarize(eid) for eid in functional_ids],
            "infrastructure": [self._summarize(eid) for eid in infrastructure_ids],
        }

    def dependents(self, id: str, recursive: bool = False) -> dict:
        """
        Get dependents of an entity.

        Returns:
            {
                "functional": [{"id", "status", "type", "criticality"}, ...],
                "infrastructure": [{"id", "status", "type"}, ...]
            }
            - if id is asset: infrastructure = who runs on it (reverse runs_on)
            - if id is non-asset: infrastructure = entities on same host(s)
        """
        if id not in self._by_id:
            raise KeyError(f"Entidad no encontrada: {id}")

        entity = self._by_id[id]
        category = entity.get("category")

        # Functional: inverse BFS over depends_on
        functional_ids = self._bfs_dependents_of(id, recursive)

        # Infrastructure: directional lookup based on entity type
        if category == "assets":
            infrastructure_ids = sorted(self._rruns_on_index.get(id, set()))
        else:
            hosts = self._runs_on_index.get(id, set())
            infrastructure_ids = []
            for host in hosts:
                infrastructure_ids.extend(self._rruns_on_index.get(host, set()))
            infrastructure_ids = sorted(set(infrastructure_ids))

        return {
            "functional": [self._summarize(eid) for eid in functional_ids],
            "infrastructure": [self._summarize(eid) for eid in infrastructure_ids],
        }

    # ─────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────

    def _summarize(self, eid: str) -> dict:
        """
        Return a minimal dict with id, status, type, and criticality.
        Used by dependencies/dependents to enrich graph queries.
        """
        entity = self._by_id.get(eid, {})
        return {
            "id": eid,
            "status": entity.get("status"),
            "type": entity.get("type"),
            "criticality": entity.get("criticality"),
        }

    def validate(self) -> dict:
        """
        Validate the entire Registry.

        Returns:
            {
                "valid": bool,
                "errors": [{"file": str, "error": str}],
                "warnings": [{"file": str, "warning": str}],
                "stats": {"total": int, "by_category": dict}
            }
        """
        errors = []
        warnings = []

        # Stats
        total = len(self._by_id)
        by_category = {cat: len(ids) for cat, ids in self._by_category.items()}

        # Check for duplicate IDs across categories
        id_locations = {}
        for eid in self._by_id:
            for cat, ids in self._by_category.items():
                if eid in ids:
                    id_locations[eid] = f"{cat}/{eid}.yaml"
                    break
        if len(id_locations) != total:
            seen = {}
            for eid, loc in id_locations.items():
                if eid in seen:
                    errors.append({
                        "file": loc,
                        "error": f"ID duplicado: {eid}"
                    })
                seen[eid] = loc

        # Check relations point to existing IDs
        for eid, entity in self._by_id.items():
            relations = entity.get("relations", {})
            for rel_type, targets in relations.items():
                if isinstance(targets, list):
                    for t in targets:
                        if t not in self._by_id:
                            errors.append({
                                "file": f"{entity.get('category')}/{eid}.yaml",
                                "error": f"relations.{rel_type}: '{t}' no existe"
                            })

        # Check entities without any relations
        for eid, entity in self._by_id.items():
            relations = entity.get("relations", {})
            has_relation = any(
                relations.get(rel, []) for rel in ["runs_on", "depends_on", "part_of"]
            )
            if not has_relation and entity.get("category") != "projects" and entity.get("category") != "endpoints":
                warnings.append({
                    "file": f"{entity.get('category')}/{eid}.yaml",
                    "warning": f"Entidad sin relaciones definidas"
                })

        # Check category match with folder
        for eid, entity in self._by_id.items():
            expected_cat = None
            for cat in self._categories:
                if eid in self._by_category[cat]:
                    expected_cat = cat
                    break
            if expected_cat and entity.get("category") != expected_cat:
                warnings.append({
                    "file": f"{expected_cat}/{eid}.yaml",
                    "warning": f"category={entity.get('category')} ≠ carpeta={expected_cat}"
                })

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": {"total": total, "by_category": by_category}
        }