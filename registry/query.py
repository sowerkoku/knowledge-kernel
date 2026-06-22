"""
Registry Query Functions — Public API

Each function wraps RegistryIndex and normalizes output.
"""

from .indexer import RegistryIndex

# Singleton index instance (lazy init)
_index: RegistryIndex = None


def _get_index() -> RegistryIndex:
    global _index
    if _index is None:
        _index = RegistryIndex()
    return _index


def registry_get(id: str) -> dict:
    """
    Get entity by ID.

    Returns:
        dict | None: Full entity if found, None otherwise.
    """
    return _get_index().get(id)


def registry_list(category: str = None) -> list[dict]:
    """
    List entities, optionally filtered by category.

    Args:
        category: assets | software | data | automation | projects | procedures | None

    Returns:
        list[dict]: Summary of each entity (id, category, type, name, status, tags)
    """
    return _get_index().list(category)


def registry_search(query: str) -> list[dict]:
    """
    Search by text in id, name, description, tags.

    Args:
        query: Search string (case-insensitive, partial match)

    Returns:
        list[dict]: Matches with id, name, category, match_field, score
    """
    return _get_index().search(query)


def registry_dependencies(id: str, recursive: bool = False) -> dict:
    """
    Get dependencies of an entity.

    Args:
        id: Entity ID
        recursive: If True, include transitive dependencies

    Returns:
        {
            "functional": sorted list of depends_on closure,
            "infrastructure": sorted list of runs_on (1-hop only)
        }
    """
    return _get_index().dependencies(id, recursive)


def registry_dependents(id: str, recursive: bool = False) -> dict:
    """
    Get entities that depend on this one.

    Args:
        id: Entity ID
        recursive: If True, include transitive dependents

    Returns:
        {
            "functional": sorted list of inverse depends_on BFS,
            "infrastructure": entities sharing same host(s)
                - if id is asset: who runs on it (reverse lookup)
                - if id is non-asset: who shares the same host(s)
        }
    """
    return _get_index().dependents(id, recursive)


def registry_validate() -> dict:
    """
    Validate the Registry.

    Returns:
        {
            "valid": bool,
            "errors": [{"file": str, "error": str}],
            "warnings": [{"file": str, "warning": str}],
            "stats": {"total": int, "by_category": dict}
        }
    """
    return _get_index().validate()