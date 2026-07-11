"""
Relation validation rules for Agent CMDB.

Validates:
- Relation type is in the catalog
- Relation target exists in the CMDB
- Relation type is compatible with target kind
- No duplicate relations
"""

from .schema import Error, Warning


# Catálogo cerrado de relaciones válidas
VALID_RELATION_TYPES = {
    "runs_on",
    "uses",
    "reads",
    "writes",
    "calls",
    "owns",
    "backs_up",
    "monitors",
    "part_of",
    "depends_on",
    "assigned_to",
    "belongs_to",
    "uses_profile",
    "listens_on",
    "exposes",
    "exposed_by",
}

# Reglas de compatibilidad: relation_type → target kinds válidos
RELATION_TARGET_KINDS = {
    "runs_on": {"asset"},
    "uses": None,  # Cualquier kind es válido
    "reads": {"data", "software"},
    "writes": {"data", "software"},
    "calls": {"endpoint", "software"},
    "owns": None,  # Cualquier kind es válido
    "backs_up": {"data"},
    "monitors": None,  # Cualquier kind es válido
    "exposes": {"endpoint"},  # software expone endpoint
    "exposed_by": {"software"},  # endpoint expuesto por software
}


def validate_relation_type(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate relation types are in the catalog."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    relations = entity.get("relations", [])

    if not isinstance(relations, list):
        errors.append(Error(entity_id, "relations", "Field 'relations' must be a list"))
        return errors, warnings

    seen_relations = set()

    for idx, rel in enumerate(relations):
        if not isinstance(rel, dict):
            errors.append(Error(entity_id, f"relations[{idx}]", "Relation must be an object"))
            continue

        rel_type = rel.get("type")
        rel_target = rel.get("target")

        if rel_type is None:
            errors.append(Error(entity_id, f"relations[{idx}].type", "Missing required field 'type'"))
            continue

        if rel_target is None:
            errors.append(Error(entity_id, f"relations[{idx}].target", "Missing required field 'target'"))
            continue

        if rel_type not in VALID_RELATION_TYPES:
            errors.append(Error(entity_id, f"relations[{idx}].type", f"Unknown relation type: {rel_type!r}. Valid types: {sorted(VALID_RELATION_TYPES)}"))

        # Check for duplicates
        rel_key = (rel_type, rel_target)
        if rel_key in seen_relations:
            errors.append(Error(entity_id, f"relations[{idx}]", f"Duplicate relation: {rel_type} → {rel_target}"))
        seen_relations.add(rel_key)

    return errors, warnings


def validate_relation_targets(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate relation targets exist in the CMDB."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    relations = entity.get("relations", [])

    if not isinstance(relations, list):
        return errors, warnings  # Already caught by validate_relation_type

    for idx, rel in enumerate(relations):
        if not isinstance(rel, dict):
            continue

        rel_type = rel.get("type")
        rel_target = rel.get("target")

        if rel_target is None or rel_type is None:
            continue  # Already caught

        if rel_type not in VALID_RELATION_TYPES:
            continue  # Already caught by validate_relation_type

        # Check if target exists
        if rel_target not in all_entities:
            errors.append(Error(entity_id, f"relations[{idx}].target", f"Relation target does not exist: {rel_target!r}"))

    return errors, warnings


def validate_relation_target_kinds(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Validate relation target kinds are compatible."""
    errors = []
    warnings = []

    entity_id = entity.get("id", "<unknown>")
    relations = entity.get("relations", [])

    if not isinstance(relations, list):
        return errors, warnings

    for idx, rel in enumerate(relations):
        if not isinstance(rel, dict):
            continue

        rel_type = rel.get("type")
        rel_target = rel.get("target")

        if rel_target is None or rel_type is None:
            continue

        if rel_type not in VALID_RELATION_TYPES:
            continue

        # Check target kind compatibility
        allowed_kinds = RELATION_TARGET_KINDS.get(rel_type)
        if allowed_kinds is None:
            # Any kind is valid
            continue

        if rel_target not in all_entities:
            continue  # Already caught by validate_relation_targets

        target_entity = all_entities[rel_target]
        target_kind = target_entity.get("kind")

        if target_kind not in allowed_kinds:
            errors.append(Error(
                entity_id,
                f"relations[{idx}].target",
                f"Relation {rel_type!r} requires target kind in {sorted(allowed_kinds)}, but {rel_target!r} has kind {target_kind!r}"
            ))

    return errors, warnings


def validate_all_relations(entity: dict, all_entities: dict) -> tuple[list[Error], list[Warning]]:
    """Run all relation validation rules."""
    all_errors = []
    all_warnings = []

    for validator in [
        validate_relation_type,
        validate_relation_targets,
        validate_relation_target_kinds,
    ]:
        errors, warnings = validator(entity, all_entities)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    return all_errors, all_warnings